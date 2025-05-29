import os
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from django.conf import settings

from .forms import AdminAddRealtyForm
from .models import Realty, Address, Category, Query
from .utils import get_all_employees, get_all_clients


class TestViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prev_media = settings.MEDIA_ROOT
        Group.objects.get_or_create(name='Employee')
        cls.user_model = get_user_model()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user_admin =  cls.user_model.objects.create_superuser(username="Admin")
        cls.admin = Client()
        cls.admin.force_login(cls.user_admin)
        cls.user_employee =  cls.user_model.objects.create(username="Employee")
        employee_group = Group.objects.get(name='Employee')
        cls.user_employee.groups.add(employee_group)
        cls.employee = Client()
        cls.employee.force_login(cls.user_employee)
        cls.user1 =  cls.user_model.objects.create(username="User1")
        cls.client1 = Client()
        cls.client1.force_login(cls.user1)
        cls.user2 =  cls.user_model.objects.create(username="User2")
        cls.client2 = Client()
        cls.client2.force_login(cls.user2)
        cls.testCategory = Category.objects.create(name="TestCategory", slug="TestCategory")
        image_content = b'...'
        image_temp_file = tempfile.NamedTemporaryFile(delete=False)
        image_temp_file.write(image_content)
        image_temp_file.close()

        cls.uploaded_file = SimpleUploadedFile(
            name=settings.MEDIA_ROOT+'\photos\pest_image10.jpg',
            content=open(image_temp_file.name, 'rb').read(),
            content_type='image/jpeg'
        )
        cls.testAddress = Address.objects.create(state="Minsk", city="Minsk", address="Filimonova 43A")
        cls.test_agency_realty = Realty.objects.create(name="TestAgencyRealty", slug="TestAgencyRealty",
                                                      price=2000, cat=cls.testCategory, description="TestAgencyRealty desc", photo=cls.uploaded_file, owner=cls.user_employee, address=cls.testAddress)

        cls.test_user_realty = Realty.objects.create(name="TestUserRealty", slug="TestUserRealty",
                                                     price=2000, cat=cls.testCategory,
                                                     description="TestUserRealty desc", photo=cls.uploaded_file,
                                                     owner=cls.user1, address=cls.testAddress)


    def test_main(self):
        response = self.client1.get(reverse('main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'agency/base.html')


    def test_user_realties(self):
        response = self.client2.get(reverse('users_realty'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('realties', response.context)
        self.assertEqual(response.context['realties'][0], self.test_user_realty)
        self.assertEqual(response.context['cats'][0], self.testCategory)
        self.assertEqual(response.context['Agency'], False)
        self.assertTemplateUsed(response, 'agency/realties.html')

    def test_agency_realties(self):
        response = self.client2.get(reverse('agency_realty'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('realties', response.context)
        self.assertEqual(response.context['realties'][0], self.test_agency_realty)
        self.assertEqual(response.context['cats'][0], self.testCategory)
        self.assertEqual(response.context['Agency'], True)
        self.assertTemplateUsed(response, 'agency/realties.html')

    def test_agency_category_realties(self):
        response = self.client2.get(reverse('agency_category', kwargs={'category_slug': self.testCategory.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['realties'][0], self.test_agency_realty)
        self.assertEqual(response.context['cats'][0], self.testCategory)
        self.assertEqual(response.context['cat_selected'], self.testCategory)
        self.assertEqual(response.context['Agency'], True)
        self.assertTemplateUsed(response, 'agency/category.html')

    def test_user_category_realties(self):
        response = self.client2.get(reverse('user_category', kwargs={'category_slug': self.testCategory.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['realties'][0], self.test_user_realty)
        self.assertEqual(response.context['cats'][0], self.testCategory)
        self.assertEqual(response.context['cat_selected'], self.testCategory)
        self.assertEqual(response.context['Agency'], False)
        self.assertTemplateUsed(response, 'agency/category.html')

    def test_view_realty(self):
        response = self.client2.get(reverse('realty', kwargs={'realty_slug': self.test_user_realty.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['realty'], self.test_user_realty)
        self.assertTemplateUsed(response, 'agency/realty.html')

    def test_owner_user_realty(self):
        response = self.client2.get(reverse('owner_realties'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('owner_buying_realties', response.context)
        self.assertIn('owner_not_buying_realties', response.context)
        self.assertIn('buying_realties', response.context)
        self.assertIn('must_pay_realties', response.context)
        self.assertIn('cats', response.context)
        self.assertEqual(response.context['cats'][0],self.testCategory)
        self.assertTemplateUsed(response, 'agency/owner_realty.html')

    def test_owner_agency_realty(self):
        response = self.employee.get(reverse('owner_realties'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('owner_buying_realties', response.context)
        self.assertIn('owner_not_buying_realties', response.context)
        self.assertIn('cats', response.context)
        self.assertEqual(response.context['cats'][0],self.testCategory)
        self.assertTemplateUsed(response, 'agency/owner_realty.html')

    def test_query_agency(self):
        response = self.employee.get(reverse('query'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('querys_to', response.context)
        self.assertIn('cats', response.context)
        self.assertEqual(response.context['cats'][0],self.testCategory)
        self.assertTemplateUsed(response, 'agency/query.html')

    def test_query_user(self):
        response = self.client2.get(reverse('query'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('querys_to', response.context)
        self.assertIn('querys_from', response.context)
        self.assertIn('cats', response.context)
        self.assertEqual(response.context['cats'][0],self.testCategory)
        self.assertTemplateUsed(response, 'agency/query.html')

    def test_create_query(self):
        response = self.client2.get(reverse('create_quary', kwargs={'realty_slug':self.test_user_realty.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/query/')
        response = self.client2.get(reverse('query'))
        self.assertIn('querys_to', response.context)
        self.assertEqual(response.context['querys_from'][0].realty, self.test_user_realty)
        self.assertEqual(response.context['querys_from'][0].landlord, self.user2)
        self.assertIn('querys_to', response.context)
        self.assertIn('cats', response.context)
        self.assertEqual(response.context['cats'][0],self.testCategory)
        self.assertTemplateUsed(response, 'agency/query.html')

    def test_user_accept_query(self):
        response = self.client2.get(reverse('create_quary', kwargs={'realty_slug':self.test_user_realty.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/query/')
        response = self.client1.get(reverse('query'))
        response = self.client1.get(reverse('accept_query', kwargs={'query_id': response.context['querys_to'][0].id}))
        self.assertEqual(response.context['realty'], self.test_user_realty)
        self.assertEqual(response.context['landlord'], self.user2)
        self.assertTemplateUsed(response, 'agency/pay_accept_query.html')

    def test_pay_accept_query(self):
        response = self.client2.get(reverse('create_quary', kwargs={'realty_slug':self.test_user_realty.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/query/')
        response = self.client1.get(reverse('query'))
        response = self.client1.get(reverse('accept_query', kwargs={'query_id': response.context['querys_to'][0].id}))
        response = self.client2.get(reverse('success', kwargs={'realty_slug':response.context['realty'].slug, 'landlord_id':response.context['landlord'].id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        test_user_realty = Realty.objects.get(slug=self.test_user_realty.slug)
        self.assertEqual(test_user_realty.landlord, self.user2)
        self.assertEqual(test_user_realty.is_sold, True)

    def test_agency_accept_query(self):
        response = self.client2.get(reverse('create_quary', kwargs={'realty_slug':self.test_agency_realty.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/query/')
        response = self.employee.get(reverse('query'))
        response = self.employee.get(reverse('accept_query', kwargs={'query_id': response.context['querys_to'][0].id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/query/')
        test_agency_realty = Realty.objects.get(slug=self.test_agency_realty.slug)
        self.assertEqual(test_agency_realty.landlord, self.user2)
        self.assertEqual(test_agency_realty.is_sold, False)

    def test_view_buy_realty(self):
        response = self.client1.get(reverse('buy_realty', kwargs={'realty_slug': self.test_agency_realty.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['realty'], self.test_agency_realty)
        self.assertEqual(response.context['landlord'], self.user1)
        self.assertIn("STRIPE_PUBLIC_KEY", response.context)

    def test_pay_agency_realty(self):
        response = self.client2.get(reverse('create_quary', kwargs={'realty_slug':self.test_agency_realty.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/query/')
        response = self.employee.get(reverse('query'))
        response = self.employee.get(reverse('accept_query', kwargs={'query_id': response.context['querys_to'][0].id}))
        response = self.client2.get(reverse('owner_realties'))

        response = self.client2.get(reverse('success', kwargs={'realty_slug':response.context['must_pay_realties'][0].slug, 'landlord_id':self.user2.id}))
        test_agency_realty = Realty.objects.get(slug=self.test_agency_realty.slug)
        self.assertEqual(test_agency_realty.is_sold, True)

    def test_create_checkout_session(self):
        response = self.client1.post(reverse('create-checkout-session', kwargs={'realty_slug': self.test_user_realty.slug, 'landlord_id': self.user1.id}))
        self.assertEqual(response.status_code, 302)

    def test_cancel_checkout_session(self):
        response = self.client1.get(reverse('cancel'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_admin_add_realty(self):
        new_category = Category.objects.create(name='New Category')

        form_data = {
            'name': 'Test Realty',
            'description': 'Test Description',
            'price': 1000,
            'category': new_category.id,
            'city': 'Test City',
            'state': 'Test State',
            'address': 'Test Address',
            'employee': self.user_employee.id
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media+'/'+'default_avatar.png',
            content=open(self.prev_media+'/'+'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.admin.post(reverse('add_realty'), data=form_data|form_files)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Realty.objects.filter(name='Test Realty').exists())

    def test_user_add_realty(self):

        form_data = {
            'name': 'Test User Realty',
            'description': 'Test Description',
            'price': 1000,
            'category': self.testCategory.id,
            'city': 'Test City',
            'state': 'Test State',
            'address': 'Test Address',
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media+'/'+'default_avatar.png',
            content=open(self.prev_media+'/'+'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.client1.post(reverse('add_realty'), data=form_data|form_files)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Realty.objects.filter(name='Test User Realty').exists())

    def test_user_update_realty(self):

        form_data = {
            'name': self.test_user_realty.name,
            'description': self.test_user_realty.description,
            'price': self.test_user_realty.price,
            'category': self.testCategory.id,
            'city': 'New City',
            'state': 'New State',
            'address': 'New Address',
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media+'/'+'default_avatar.png',
            content=open(self.prev_media+'/'+'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.client1.post(reverse('update_realty', args=[self.test_user_realty.slug]), data=form_data|form_files)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Realty.objects.get(name=self.test_user_realty.name).address.city, 'New City')

    def test_admin_update_realty(self):

        form_data = {
            'name': self.test_agency_realty.name,
            'description': self.test_agency_realty.description,
            'price': self.test_agency_realty.price,
            'category': self.testCategory.id,
            'city': 'New City',
            'state': 'New State',
            'address': 'New Address',
            'employee': self.user_employee.id
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media+'/'+'default_avatar.png',
            content=open(self.prev_media+'/'+'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.admin.post(reverse('update_realty', args=[self.test_agency_realty.slug]), data=form_data|form_files)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Realty.objects.get(name=self.test_agency_realty.name).address.city, 'New City')

    def test_delete_realty(self):
        form_data = {
            'name': 'Temp_Realty',
            'description': 'Test Description',
            'price': 1000,
            'category': self.testCategory.id,
            'city': 'Test City',
            'state': 'Test State',
            'address': 'Test Address',
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media + '/' + 'default_avatar.png',
            content=open(self.prev_media + '/' + 'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.client1.post(reverse('add_realty'), data=form_data | form_files)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Realty.objects.filter(name='Temp_Realty').exists())
        self.client1.get(reverse('delete_realty', args=[Realty.objects.get(name='Temp_Realty').slug]))
        self.assertFalse(Realty.objects.filter(name='Temp_Realty').exists())


    def test_delete_query(self):
        response = self.client2.get(reverse('create_quary', kwargs={'realty_slug': self.test_user_realty.slug}))
        response = self.client2.get(reverse('query'))
        query = response.context['querys_from'][0]
        response = self.client2.get(reverse('delete_query', args=[query.id]))
        self.assertFalse(Query.objects.filter(id=query.id).exists())

    def test_admin_info(self):
        response = self.admin.get(reverse('admin_info'))
        self.assertTemplateUsed(response,'agency/owner/admin_info.html' )
        self.assertEqual(response.status_code, 200)
        self.assertIn('realties_prices', response.context)
        self.assertIn('prices', response.context)
        self.assertIn('average', response.context)
        self.assertIn('mode', response.context)
        self.assertIn('mediana', response.context)
        self.assertIn('average_date', response.context)
        self.assertIn('mediana_date', response.context)
        self.assertIn('all_category', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('categories_price', response.context)
        self.assertIn('most_popular_category', response.context)
        self.assertIn('most_beneficial_category', response.context)


    def test_provile_user(self):
        response = self.client1.get(reverse('profile_user', args=[self.user1.id]))
        self.assertTemplateUsed(response,'agency/profile_user.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('realtys', response.context)
        self.assertEqual(response.context['user'],self.user1)

    def test_update_user(self):
        form_data =  {
            'username': 'john_doe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '(29)3456789',
            'date': '1990-01-01',  # Формат даты: ГГГГ-ММ-ДД
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media + '/' + 'default_avatar.png',
            content=open(self.prev_media + '/' + 'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.client1.post(reverse('update_user_data', args=[self.user1.id]),
                                     data=form_data | form_files)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user_model.objects.get(id=self.user1.id).username, 'Updated Name')

    def test_view_all_realties(self):
        response = self.admin.get(reverse('all_realties'))
        self.assertTemplateUsed(response, 'agency/owner/all_realties.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('sold_realties', response.context)
        self.assertIn('not_sold_realties', response.context)
        self.assertEqual(response.context['employees'][0], self.user_employee)

    def test_user_view_all_realties(self):
        response = self.client1.get(reverse('all_realties'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_view_all_employees(self):
        response = self.admin.get(reverse('all_employees'))
        self.assertTemplateUsed(response, 'agency/owner/all_employees.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('employee_realties', response.context)
        self.assertEqual(response.context['all_employees'][0], self.user_employee)

    def test_user_view_all_employees(self):
        response = self.client1.get(reverse('all_employees'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_view_all_clients(self):
        response = self.admin.get(reverse('all_clients'))
        self.assertTemplateUsed(response, 'agency/owner/all_clients.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('client_realties', response.context)
        self.assertEqual(set(response.context['all_clients']),set(get_all_clients()))


    def test_user_view_all_clients(self):
        response = self.client1.get(reverse('all_clients'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_add_employees(self):
        form_data = {
            'username': 'john_doe',
            'first_name': 'John',
            'password1': 'dsfsfm3jjwdm,!jhsdfhskdfSDJF',
            'password2': 'dsfsfm3jjwdm,!jhsdfhskdfSDJF',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '(29)3456789',
            'date': '1990-01-01',  # Формат даты: ГГГГ-ММ-ДД
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media + '/' + 'default_avatar.png',
            content=open(self.prev_media + '/' + 'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.admin.post(reverse('add_employee'),
                                     data=form_data | form_files)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user_model.objects.get(username='john_doe'), get_all_employees())


    def test_delete_employee(self):
        form_data = {
            'username': 'john_doe1',
            'first_name': 'John',
            'password1': 'dsfsfm3jjwdm,!jhsdfhskdfSDJF',
            'password2': 'dsfsfm3jjwdm,!jhsdfhskdfSDJF',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '(29)3456789',
            'date': '1990-01-01',  # Формат даты: ГГГГ-ММ-ДД
        }
        uploaded_file = SimpleUploadedFile(
            name=self.prev_media + '/' + 'default_avatar.png',
            content=open(self.prev_media + '/' + 'default_avatar.png', 'rb').read(),
            content_type='image/jpeg'
        )
        form_files = {
            'photo': uploaded_file
        }
        response = self.admin.post(reverse('add_employee'),
                                   data=form_data | form_files)
        emp = self.user_model.objects.get(username='john_doe1')
        response = self.admin.get(reverse('delete_employee', args=[emp.id]))
        self.assertFalse(self.user_model.objects.filter(username='john_doe').exists())

    def test_user_delete_employee(self):
        response = self.client1.get(reverse('delete_employee', args=[self.user_employee.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_employee_clients(self):
        response = self.employee.get(reverse('employee_clients', args=[self.user_employee.id]))
        self.assertTemplateUsed(response, 'agency/employee_clients.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('all_clients', response.context)
        self.assertIn('client_realties', response.context)

    def test_user_employee_clients(self):
        response = self.client1.get(reverse('employee_clients', args=[self.user_employee.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')





def tearDownModule():
    print("\nDeleting temporary files...\n")
    try:
        shutil.rmtree(settings.MEDIA_ROOT)
    except OSError:
        pass
