from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import *
from .utils import get_all_employees
from dateutil.relativedelta import relativedelta



class DateInput(forms.DateInput):
    input_type='date'


class BaseRealtyForm(forms.ModelForm):
    name = forms.CharField(label='Название', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Название'}))
    description = forms.CharField(label='Описание', widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Описание', 'rows': 3}))
    price = forms.IntegerField(widget=forms.NumberInput(
        attrs={'class': 'form-control', 'placeholder': 'Цена', 'min': '1',  'step': '1'}))
    photo = forms.ImageField(label='Фото', widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    category = forms.ModelChoiceField(label="Категория", queryset=Category.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    state = forms.CharField(label='Регион', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Регион'}))
    city = forms.CharField(label='Город', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Город'}))
    address = forms.CharField(label='Адрес', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Адрес'}))
    class Meta:
        model = Realty
        fields = ('name', 'description', 'price', 'photo', 'category')


class AdminAddRealtyForm(BaseRealtyForm):
    employee = forms.ModelChoiceField(label="Сотрудник", queryset=get_all_employees(), widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta(BaseRealtyForm.Meta):
        fields = BaseRealtyForm.Meta.fields + ('employee',)

class AddRealtyForm(BaseRealtyForm):
    pass

class AdminUpdateRealtyForm(BaseRealtyForm):
    employee = forms.ModelChoiceField(label="Сотрудник", queryset=get_all_employees(), widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta(BaseRealtyForm.Meta):
        fields = BaseRealtyForm.Meta.fields + ('employee',)

class UpdateRealtyForm(BaseRealtyForm):
    pass

def validate_age_18(date):
    import datetime
    from django.utils import timezone
    now_dt = timezone.now()
    # Дата рождения в будущем — ошибка
    if date > now_dt.date():
        raise forms.ValidationError('Дата рождения не может быть в будущем.')
    # Считаем, что время рождения 00:00 (если не указано)
    birth_dt = datetime.datetime.combine(date, datetime.time.min, tzinfo=now_dt.tzinfo)
    # Дата, когда исполнится 18 лет
    dt_18 = birth_dt + relativedelta(years=18)
    if now_dt < dt_18:
        raise forms.ValidationError('Вам должно быть не менее 18 лет (с точностью до минут) для регистрации.')
    return date

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}))
    first_name = forms.CharField(label='Имя', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Имя'}))
    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Фамилия'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Пароль'}))
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}))
    phone_number = forms.CharField(label='Телефон', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Телефон'}))
    date = forms.DateField(label='Дата рождения', widget=DateInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(label='Фото профиля', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    def clean_date(self):
        date = self.cleaned_data['date']
        return validate_age_18(date)
    class Meta:
        model = User
        fields = ('username', 'first_name','last_name', 'email', 'password1', 'password2','date', 'phone_number', 'photo')


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder':'Пароль'}))


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}))
    first_name = forms.CharField(label='Имя', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Имя'}))
    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Фамилия'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone_number = forms.CharField(label='Телефон', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Телефон'}))
    date = forms.DateField(label='Дата рождения',widget=DateInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(label='Фото профиля', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    def clean_date(self):
        date = self.cleaned_data['date']
        return validate_age_18(date)
    class Meta:
        model = User
        fields = ('username', 'first_name','last_name', 'email', 'date', 'phone_number', 'photo')


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Ваш отзыв'}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control', 'placeholder': 'Оценка (1-5)'}),
        }

class ArticleForm(forms.ModelForm):
    title = forms.CharField(label='Заголовок', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Заголовок'}))
    text = forms.CharField(label='Текст', widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Текст новости', 'rows': 5}))
    photo = forms.ImageField(label='Фото новости', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Article
        fields = ['title', 'text', 'photo']