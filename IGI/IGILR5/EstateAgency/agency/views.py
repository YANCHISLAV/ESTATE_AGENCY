"""
Views for the Agency application.
Оптимизировано: убраны дубли, вынесены общие блоки, приведено к единому стилю.
"""

# Standard Library
import datetime
import logging
import os
import statistics
from typing import Dict, List

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import stripe
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .forms import (
    LoginUserForm, RegisterUserForm, AddRealtyForm, AdminAddRealtyForm,
    AdminUpdateRealtyForm, UpdateRealtyForm, UpdateUserForm, ReviewForm, ArticleForm
)
from .models import Address, Category, Query, Realty, Transaction, PromoCode, Article
from .utils import get_ip_adress, get_info_user_by_ip, get_all_employees, get_all_clients, filter_sort_realties

main_logger = logging.getLogger('main')
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- Утилиты для повторяющихся действий ---
def send_email(subject, message, recipient_list):
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
    except Exception as ex:
        main_logger.error(f"Failed to send email to {recipient_list}: {str(ex)}")

def process_promocode(request):
    promocode = request.GET.get('promocode')
    if not promocode:
        return -1
    try:
        promo = PromoCode.objects.filter(code=promocode).first()
        if not promo:
            raise PromoCode.DoesNotExist
        discount = promo.discount
        request.session['discount'] = discount
        messages.success(request, f"Промокод применён. Скидка: {discount}%")
        return discount
    except PromoCode.DoesNotExist:
        messages.error(request, f"Некорректный промокод: {promocode}")
        main_logger.error(f"Invalid promocode attempt: {promocode}")
        if 'discount' in request.session:
            del request.session['discount']
        return -1

def get_price_with_discount(request, realty):
    if realty.owner not in get_all_employees():
        price = realty.price
    else:
        price = realty.price * 100
    discount = request.session.get('discount')
    if discount:
        price = int(price * (1 - discount / 100))
    return price

# --- FBV для простых страниц ---
def main(request):
    return TemplateResponse(request, 'agency/base.html')

def cancel(request):
    messages.info(request, "Платёж отменён.")
    return redirect('main')

# --- Авторизация и регистрация ---
class CustomLoginView(LoginView):
    form_class = LoginUserForm
    template_name = 'agency/login.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Login"
        return context
    def get_success_url(self):
        main_logger.info(f"User authenticated: {self.request.user.username}")
        return reverse_lazy('main')
    def form_invalid(self, form):
        main_logger.debug(f'Invalid login data: {form.errors}')
        return super().form_invalid(form)

class RegisterUserView(CreateView):
    form_class = RegisterUserForm
    template_name = 'agency/register.html'
    success_url = reverse_lazy('login')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Create Employee" if self.request.user.is_superuser else "Register"
        return context
    def form_valid(self, form):
        user = form.save()
        if self.request.user.is_superuser:
            employee_group = Group.objects.get(name='Employee')
            user.groups.add(employee_group)
            user.save()
            messages.success(self.request, f"Employee created: {user.username}")
            main_logger.info(f"Employee registered: {user.username}")
        else:
            login(self.request, user)
            main_logger.info(f"User registered: {user.username}")
        return redirect('main')
    def form_invalid(self, form):
        main_logger.debug(f'Invalid registration data: {form.errors}')
        return super().form_invalid(form)

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        main_logger.debug(f"Logging out user: {request.user.username}")
        logout(request)
        return redirect('main')

# --- Список и детали недвижимости ---
class RealtyListView(ListView):
    template_name = 'agency/realties.html'
    context_object_name = 'realties'
    def get_queryset(self):
        is_agency = self.request.GET.get('agency', '0') == '1'
        all_employees = get_all_employees()
        if is_agency:
            realties = Realty.objects.filter(landlord__isnull=True, owner__in=all_employees)
        else:
            realties = Realty.objects.filter(~Q(owner__in=all_employees), landlord__isnull=True)
        realties = filter_sort_realties(self.request, realties)
        if self.request.user.is_authenticated:
            realties = realties.filter(~Q(owner=self.request.user))
        return realties
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Agency'] = self.request.GET.get('agency', '0') == '1'
        context['cats'] = Category.objects.all()
        return context

class RealtyDetailView(View):
    def get(self, request, realty_slug: str):
        realty = get_object_or_404(Realty, slug=realty_slug)
        return TemplateResponse(request, 'agency/realty.html', {'realty': realty})

# --- Категории ---
class CategoryRealtyView(ListView):
    template_name = 'agency/category.html'
    context_object_name = 'realties'
    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        cat = get_object_or_404(Category, slug=category_slug)
        all_employees = get_all_employees()
        is_agency = self.request.GET.get('agency', '0') == '1'
        if is_agency:
            realties = Realty.objects.filter(landlord__isnull=True, cat=cat, owner__in=all_employees)
        else:
            realties = Realty.objects.filter(~Q(owner__in=all_employees), landlord__isnull=True, cat=cat)
        if self.request.user.is_authenticated:
            realties = realties.filter(~Q(owner=self.request.user))
        return filter_sort_realties(self.request, realties)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cat = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        info_user = get_info_user_by_ip(get_ip_adress(self.request))
        user_city = info_user.get('city')
        realties = context['realties']
        realties_city_user = realties.filter(address__city=user_city) if user_city else None
        context.update({
            'Agency': self.request.GET.get('agency', '0') == '1',
            'cats': Category.objects.all(),
            'cat_selected': cat,
            'realtys_city_user': realties_city_user
        })
        return context

# --- CRUD недвижимости ---
class AddRealtyView(LoginRequiredMixin, CreateView):
    template_name = 'agency/add_realty.html'
    def get_form_class(self):
        return AdminAddRealtyForm if self.request.user.is_superuser else AddRealtyForm
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Realty"
        return context
    def form_valid(self, form):
        name = form.cleaned_data['name']
        description = form.cleaned_data['description']
        price = form.cleaned_data['price']
        category = form.cleaned_data['category']
        photo = form.cleaned_data['photo']
        city = form.cleaned_data['city']
        state = form.cleaned_data['state']
        address = form.cleaned_data['address']
        main_logger.info(f"Create new realty, name: {name}")
        if self.request.user.is_superuser:
            employee_username = form.cleaned_data['employee']
            owner = get_user_model().objects.get(username=employee_username)
        else:
            owner = self.request.user
        try:
            addres = Address.objects.filter(city=city, state=state, address=address)
            new_address = addres[0] if addres else Address.objects.create(city=city, state=state, address=address)
            if Realty.objects.filter(slug=slugify(name)):
                form.add_error(None, "The name must be unique")
                return self.form_invalid(form)
            Realty.objects.create(name=name, description=description, price=price, cat=category, owner=owner,
                                  photo=photo, address=new_address, slug=slugify(name))
        except Exception as ex:
            messages.error(self.request, "Ошибка при создании недвижимости")
            main_logger.critical(f"Can't create realty: {ex}")
            return self.form_invalid(form)
        return redirect('main')
    def form_invalid(self, form):
        main_logger.debug(f"Invalid data in form of create realty, errors {form.errors}")
        return super().form_invalid(form)

class UpdateRealtyView(LoginRequiredMixin, UpdateView):
    template_name = 'agency/add_realty.html'
    model = Realty
    def get_form_class(self):
        return AdminUpdateRealtyForm if self.request.user.is_superuser else UpdateRealtyForm
    def form_valid(self, form):
        name = form.cleaned_data['name']
        description = form.cleaned_data['description']
        price = form.cleaned_data['price']
        category = form.cleaned_data['category']
        photo = form.cleaned_data['photo']
        city = form.cleaned_data['city']
        state = form.cleaned_data['state']
        address = form.cleaned_data['address']
        if self.request.user.is_superuser:
            employee_username = form.cleaned_data['employee']
            owner = get_user_model().objects.get(username=employee_username)
        else:
            owner = self.request.user
        try:
            addres = Address.objects.filter(city=city, state=state, address=address)
            new_address = addres[0] if addres else Address.objects.create(city=city, state=state, address=address)
            same_name_realties = Realty.objects.filter(name=name)
            if same_name_realties and same_name_realties[0] != self.object:
                form.add_error(None, "The name must be unique")
                return self.form_invalid(form)
            self.object.name = name
            self.object.description = description
            self.object.price = price
            self.object.cat = category
            self.object.owner = owner
            self.object.photo = photo
            self.object.address = new_address
            self.object.discount = False
            self.object.price_discount = price
            self.object.slug = slugify(name)
            self.object.save()
        except Exception as ex:
            form.add_error(None, "Ошибка при обновлении недвижимости")
            main_logger.error(f"Can't update realty: {ex}")
            return self.form_invalid(form)
        return HttpResponseRedirect(self.object.get_absolute_url())
    def form_invalid(self, form):
        main_logger.debug(f"Invalid data in form of update realty, errors {form.errors}")
        return super().form_invalid(form)
    def get_success_url(self):
        return self.object.get_absolute_url()

class DeleteRealtyView(LoginRequiredMixin, View):
    def post(self, request, realty_slug):
        realty = get_object_or_404(Realty, slug=realty_slug)
        main_logger.info(f"Delete realty, Owner: {realty.owner.username}, name: {realty.name}")
        realty.delete()
        return redirect('all_realties' if request.user.is_superuser else 'owner_realties')

# --- CRUD пользователей ---
class UpdateUserView(LoginRequiredMixin, UpdateView):
    template_name = 'agency/update_user.html'
    model = get_user_model()
    form_class = UpdateUserForm
    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.object.get_absolute_url())
    def form_invalid(self, form):
        main_logger.debug(f"Invalid data in Update user form, errors {form.errors}")
        return super().form_invalid(form)
    def get_success_url(self):
        return self.object.get_absolute_url()

class DeleteUserView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser
    def post(self, request, user_id):
        user = get_object_or_404(get_user_model(), id=user_id)
        try:
            user.delete()
            messages.success(request, "User deleted successfully.")
        except Exception as ex:
            messages.error(request, "Failed to delete user.")
            main_logger.error(f"Failed to delete user {user_id}: {str(ex)}")
        return redirect('main')

# --- Запросы (Query) ---
class QueryManagementView(LoginRequiredMixin, View):
    def get(self, request, realty_slug):
        realty = get_object_or_404(Realty, slug=realty_slug)
        already_exists = Query.objects.filter(realty=realty, landlord=request.user).exists()
        return TemplateResponse(request, 'agency/create_query.html', {
            'realty': realty,
            'already_exists': already_exists,
        })
    def post(self, request, realty_slug):
        realty = get_object_or_404(Realty, slug=realty_slug)
        if not Query.objects.filter(realty=realty, landlord=request.user).exists():
            Query.objects.create(owner=realty.owner, landlord=request.user, realty=realty)
            messages.success(request, "Запрос успешно создан!")
        else:
            messages.info(request, "Вы уже отправляли запрос на эту недвижимость.")
        return redirect("realty", realty_slug=realty.slug)
    def delete(self, request, query_id):
        query = get_object_or_404(Query, id=query_id)
        main_logger.info(f"Delete query, Owner: {query.owner.username}, name: {query.realty.name}")
        query.delete()
        return redirect('main')
    def put(self, request, query_id):
        # Accept query
        query = get_object_or_404(Query, id=query_id)
        realty = query.realty
        # Отправка писем
        info_realty = f"Realty: {realty.name}\nDescription: {realty.description}\nPrice: {realty.price}"
        send_email("Accept query to buy", f"Your query to buy has been accepted\n{info_realty}", [query.landlord.email])
        send_email("Accept query to buy", f"You have accepted a query to buy\n{info_realty}", [query.owner.email])
        if request.user not in get_all_employees():
            discount = process_promocode(request)
            context = {'realty': realty, 'landlord': query.landlord}
            if discount != -1:
                context['discount'] = discount
            return TemplateResponse(request, 'agency/pay_accept_query.html', context)
        else:
            realty.landlord = query.landlord
            realty.save()
            main_logger.info(f"Employee {realty.owner} accepted query from landlord {query.landlord}")
            Query.objects.filter(realty=realty).delete()
            return redirect("main")

# --- Покупка и Stripe ---
class PaymentView(LoginRequiredMixin, View):
    def get(self, request, realty_slug):
        if request.user.is_superuser:
            messages.error(request, "Администратор не может покупать объекты недвижимости.")
            return redirect('main')
        realty = get_object_or_404(Realty, slug=realty_slug)
        context = {'realty': realty}
        promocode = request.GET.get('promocode')
        discount = None
        price_discount = realty.price
        if promocode:
            promo = PromoCode.objects.filter(code=promocode).first()
            if promo:
                discount = promo.discount
                price_discount = int(realty.price * (1 - discount / 100))
                context['discount'] = discount
                context['price_discount'] = price_discount
                context['promocode'] = promocode
            else:
                messages.error(request, f"Некорректный промокод: {promocode}")
        return render(request, 'agency/buy_realty.html', context)

    def post(self, request, realty_slug):
        if request.user.is_superuser:
            messages.error(request, "Администратор не может покупать объекты недвижимости.")
            return redirect('main')
        realty = get_object_or_404(Realty, slug=realty_slug)
        promocode = request.POST.get('promocode', '').strip()
        amount = request.POST.get('amount')
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            messages.error(request, "Введите корректную сумму.")
            return redirect('buy_realty', realty_slug=realty.slug)
        discount = None
        price_discount = realty.price
        if promocode:
            promo = PromoCode.objects.filter(code=promocode).first()
            if promo:
                discount = promo.discount
                price_discount = int(realty.price * (1 - discount / 100))
            else:
                messages.error(request, f"Некорректный промокод: {promocode}")
                return redirect('buy_realty', realty_slug=realty.slug)
        if amount != price_discount:
            messages.error(request, f"Сумма должна быть равна {price_discount}.")
            return redirect('buy_realty', realty_slug=realty.slug)
        # Совершаем покупку
        realty.landlord = request.user
        realty.is_sold = True
        realty.rented_at = timezone.now()
        realty.save()
        Transaction.objects.create(realty=realty, price=price_discount)
        Query.objects.filter(realty=realty).delete()
        messages.success(request, "Поздравляем! Вы успешно купили недвижимость.")
        return redirect('realty', realty_slug=realty.slug)

# --- Отзывы ---
class ReviewView(LoginRequiredMixin, View):
    def get(self, request, realty_slug: str):
        realty = get_object_or_404(Realty, slug=realty_slug)
        form = ReviewForm()
        return render(request, 'agency/review.html', {'form': form, 'realty': realty})
    def post(self, request, realty_slug: str):
        realty = get_object_or_404(Realty, slug=realty_slug)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.realty = realty
            review.save()
            messages.success(request, 'Review added successfully.')
            return redirect('realty', realty_slug=realty.slug)
        messages.error(request, 'There was a problem with your review.')
        return render(request, 'agency/review.html', {'form': form, 'realty': realty})

# --- Админ-статистика ---
class AdminManagementView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser
    def get(self, request):
        transactions = Transaction.objects.all().order_by('realty__name')
        prices = [t.price for t in transactions]
        categories = Category.objects.all()
        price_stats = {'average': statistics.mean(prices) if prices else 0,
                       'mode': statistics.mode(prices) if prices else 0,
                       'mediana': statistics.median(prices) if prices else 0}
        employee_group = Group.objects.get(name='Employee')
        dates = [relativedelta(datetime.date.today(), user.date).years for user in get_user_model().objects.filter(is_superuser=False) if employee_group not in user.groups.all()]
        age_stats = {'average_date': statistics.mean(dates) if dates else 0,
                     'mediana_date': statistics.median(dates) if dates else 0}
        cat_counts = {cat.name: 0 for cat in categories}
        cat_prices = {cat.name: 0 for cat in categories}
        for t in transactions:
            cat_counts[t.realty.cat.name] += 1
            cat_prices[t.realty.cat.name] += t.price
        most_popular_category = max(cat_counts, key=cat_counts.get) if cat_counts else None
        most_beneficial_category = max(cat_prices, key=cat_prices.get) if cat_prices else None
        # Графики
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=30)
        dates_hist = [t.realty.rented_at.strftime("%d-%m") for t in transactions if t.realty.rented_at and start_date <= t.realty.rented_at <= end_date]
        category_hist = [t.realty.cat.name for t in transactions]
        plt.clf()
        plt.hist(dates_hist, bins=31)
        plt.xlabel('Dates')
        plt.ylabel('Count of Rented Realty')
        plt.title(f'Count of Rented Realty from {start_date.strftime("%B %d, %y")}, to {end_date.strftime("%B %d, %y")}')
        graphics_dir = os.path.join(settings.MEDIA_ROOT, 'graphics')
        os.makedirs(graphics_dir, exist_ok=True)
        plt.savefig(os.path.join(graphics_dir, 'seil_realties_by_dates.png'))
        plt.clf()
        plt.hist(category_hist, bins=len(set(category_hist)))
        plt.xlabel('Category')
        plt.ylabel('Count of Rented Realty')
        plt.title('Count of Rented Realty by Category')
        plt.savefig(os.path.join(graphics_dir, 'seil_realties_by_cat.png'))
        context = {
            **price_stats, **age_stats,
            'categories': cat_counts,
            'categories_price': cat_prices,
            'most_popular_category': most_popular_category,
            'most_beneficial_category': most_beneficial_category,
            'all_category': categories,
            'graphic1': settings.MEDIA_URL + 'graphics/seil_realties_by_dates.png',
            'graphic2': settings.MEDIA_URL + 'graphics/seil_realties_by_cat.png',
            'realties_prices': {t.realty: t.price for t in transactions}
        }
        return TemplateResponse(request, 'agency/owner/admin_info.html', context)

class NewsView(View):
    def get(self, request):
        articles = Article.objects.order_by('-created_at')
        form = ArticleForm()
        return render(request, 'agency/news.html', {'articles': articles, 'form': form})

    def post(self, request):
        if not request.user.is_superuser:
            messages.error(request, 'Только администратор может добавлять или удалять новости.')
            return redirect('news')
        if 'delete' in request.POST:
            article_id = request.POST.get('article_id')
            try:
                article = Article.objects.get(id=article_id)
                article.delete()
                messages.success(request, 'Новость удалена.')
            except Article.DoesNotExist:
                messages.error(request, 'Новость не найдена.')
            return redirect('news')
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.publisher = request.user
            article.save()
            messages.success(request, 'Новость успешно добавлена!')
        else:
            messages.error(request, 'Ошибка при добавлении новости.')
        return redirect('news')

class PrivacyView(View):
    def get(self, request):
        return render(request, 'agency/privacy.html')



