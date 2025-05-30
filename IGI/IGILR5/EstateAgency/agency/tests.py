import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import Realty, Category, Address, User, Review

pytestmark = pytest.mark.django_db

@pytest.fixture
def user(client):
    user = get_user_model().objects.create_user(username='testuser', password='testpass', email='test@example.com')
    return user

@pytest.fixture
def admin(client):
    admin = get_user_model().objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
    return admin

@pytest.fixture
def category():
    return Category.objects.create(name='Квартира', slug='kvartira')

@pytest.fixture
def address():
    return Address.objects.create(state='Минск', city='Минск', address='Победителей 1')

@pytest.fixture
def realty(user, category, address):
    image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')
    return Realty.objects.create(
        name='Test Realty',
        slug='test-realty',
        description='Описание',
        price=1000,
        photo=image,
        cat=category,
        owner=user,
        address=address
    )


def test_main_page(client):
    url = reverse('main')
    resp = client.get(url)
    assert resp.status_code == 200
    assert b'Agency Realty' in resp.content

def test_realties_list(client, realty):
    url = reverse('realties')
    resp = client.get(url)
    assert resp.status_code == 200
    assert realty.name.encode() in resp.content

def test_realties_filter_by_name(client, realty):
    url = reverse('realties') + '?search_name=Test'
    resp = client.get(url)
    assert realty.name.encode() in resp.content
    url = reverse('realties') + '?search_name=NotFound'
    resp = client.get(url)
    assert 'Нет объектов'.encode() in resp.content or realty.name.encode() not in resp.content

def test_realties_filter_by_price(client, realty):
    url = reverse('realties') + '?min_price=900&max_price=1100'
    resp = client.get(url)
    assert realty.name.encode() in resp.content
    url = reverse('realties') + '?min_price=2000'
    resp = client.get(url)
    assert 'Нет объектов'.encode() in resp.content or realty.name.encode() not in resp.content

def test_realties_filter_by_category(client, realty, category):
    url = reverse('realties') + f'?category={category.id}'
    resp = client.get(url)
    assert realty.name.encode() in resp.content
    url = reverse('realties') + '?category=9999'
    resp = client.get(url)
    assert 'Нет объектов'.encode() in resp.content or realty.name.encode() not in resp.content

def test_realty_detail(client, realty):
    url = reverse('realty', kwargs={'realty_slug': realty.slug})
    resp = client.get(url)
    assert resp.status_code == 200
    assert realty.name.encode() in resp.content

def test_register(client):
    url = reverse('register')
    data = {
        'username': 'newuser',
        'first_name': 'Имя',
        'last_name': 'Фамилия',
        'email': 'new@example.com',
        'password1': 'Testpass123!',
        'password2': 'Testpass123!',
        'phone_number': '(29)1234567',
        'date': '2000-01-01',
    }
    resp = client.post(url, data)
    assert resp.status_code in (302, 200)
    assert get_user_model().objects.filter(username='newuser').exists()

def test_login(client, user):
    url = reverse('login')
    resp = client.post(url, {'username': user.username, 'password': 'testpass'})
    assert resp.status_code in (302, 200)

def test_add_realty_admin(client, admin, category, address):
    client.force_login(admin)
    url = reverse('add_realty')
    image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')
    data = {
        'name': 'Admin Realty',
        'description': 'desc',
        'price': 2000,
        'category': category.id,
        'state': address.state,
        'city': address.city,
        'address': address.address,
        'employee': admin.id,
        'photo': image,
    }
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200
    assert Realty.objects.filter(name='Admin Realty').exists()

def test_add_realty_user(client, user, category, address):
    client.force_login(user)
    url = reverse('add_realty')
    image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')
    data = {
        'name': 'User Realty',
        'description': 'desc',
        'price': 1500,
        'category': category.id,
        'state': address.state,
        'city': address.city,
        'address': address.address,
        'photo': image,
    }
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200
    assert Realty.objects.filter(name='User Realty').exists()

def test_review_add(client, user, realty):
    client.force_login(user)
    url = reverse('add_review', kwargs={'realty_slug': realty.slug})
    data = {'text': 'Отлично!', 'rating': 5}
    resp = client.post(url, data)
    assert resp.status_code in (302, 200)
    assert Review.objects.filter(user=user, realty=realty, text='Отлично!').exists() 