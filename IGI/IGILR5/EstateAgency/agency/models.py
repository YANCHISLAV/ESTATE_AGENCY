import django
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.conf import settings
import datetime




class User(AbstractUser):
    date = models.DateField(null=True, validators=[MaxValueValidator(limit_value=datetime.date.today() - datetime.timedelta(days=18*365),   message="You must be 18 or older to use this service")])
    phone_regex = RegexValidator(regex=r'^(\+375)?\((29|33|25)\)\d{7}$',
                                 message="Phone number must be entered in the format: '+375(29)XXXXXX'")
    phone_number = models.CharField(validators=[phone_regex], max_length=15, blank=True)
    photo = models.ImageField(upload_to='avatars', default='default_avatar.png')
    def get_absolute_url(self):
        return reverse('profile_user', kwargs={'pk': self.id})

    def delete_employee_url(self):
        return reverse('delete_employee', kwargs={'user_id': self.id})

    def update_data_url(self):
        return reverse('update_user_data', kwargs={'pk': self.id})

    def display_status(self):
        if self.is_superuser:
            return 'Super User'
        elif 'Employee' in [group.name for group in self.groups.all()]:
            return 'Employee'
        else:
            return 'Client'



class Address(models.Model):
    id = models.AutoField(primary_key=True)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    def __str__(self):
        return f"Address: {self.address} with id: {self.id}"

class Realty(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    photo = models.ImageField(upload_to="photos")
    cat = models.ForeignKey('Category', on_delete=models.PROTECT)
    owner = models.ForeignKey('User',on_delete=models.PROTECT, related_name="Owner")
    landlord = models.ForeignKey('User', blank=True, null=True, on_delete=models.SET_NULL, related_name="Landbord")
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True,auto_now=True)
    rented_at = models.DateTimeField(null=True, blank=True)
    address = models.ForeignKey('Address',  on_delete=models.PROTECT)
    is_sold = models.BooleanField(default=False)
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('realty', kwargs={'realty_slug': self.slug})

    def delete_url(self):
        return reverse('delete_realty', kwargs={'realty_slug': self.slug})

    def update_url(self):
        return reverse('update_realty', kwargs={'slug': self.slug})

    def buy_url(self):
        return reverse('buy_realty', kwargs={'realty_slug': self.slug})

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    def __str__(self):
        return self.name

    def get_absolute_agency_url(self):
        return reverse('category_realties', kwargs={'category_slug': self.slug})

    def get_absolute_user_url(self):
        return reverse('category_realties', kwargs={'category_slug': self.slug})

class Query(models.Model):
    id = models.AutoField(primary_key=True)
    realty = models.ForeignKey('Realty', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    landlord = models.ForeignKey('User',on_delete=models.CASCADE, related_name="query_landlord")
    owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name="query_owner")
    def __str__(self):
        return f"Query from {self.landlord} to {self.owner} realty {self.realty}"

    def accept_query_url(self):
        return reverse('accept_query', kwargs={'query_id': self.id})

    def delete_url(self):
        return reverse('delete_query', kwargs={'query_id': self.id})







class Transaction(models.Model):
    def __str__(self):
        return f"Transaction  with realty: {self.realty}, user pay: {self.price}"
    id = models.AutoField(primary_key=True)
    realty = models.ForeignKey('Realty', on_delete=models.CASCADE)
    price = models.IntegerField()

class Article(models.Model):
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    id = models.AutoField(primary_key=True)
    publisher = models.ForeignKey('User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()

class InformationCompany(models.Model):
    information = models.TextField()


class Question(models.Model):
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    id = models.AutoField(primary_key=True)
    text = models.TextField()

class Answer(models.Model):
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    id = models.AutoField(primary_key=True)
    text = models.TextField()
    question = models.ForeignKey('Question', on_delete=models.CASCADE)

class PrivacyPolicy(models.Model):
    text = models.TextField()

class Vacancy(models.Model):
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    realty = models.ForeignKey(Realty, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.text[:50]}'

class PromoCode(models.Model):
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    discount = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(100)])
