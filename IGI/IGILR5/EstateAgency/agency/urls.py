from django.contrib import admin
from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    # Список недвижимости (агентство/пользователи через GET-параметр agency)
    path('realties/', views.RealtyListView.as_view(), name='realties'),
    path('category/<slug:category_slug>/', views.CategoryRealtyView.as_view(), name='category_realties'),
    path('realty/<slug:realty_slug>/', views.RealtyDetailView.as_view(), name='realty'),

    # Авторизация и регистрация
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # CRUD недвижимости
    path('add_realty/', views.AddRealtyView.as_view(), name='add_realty'),
    path('update_realty/<slug:slug>/', views.UpdateRealtyView.as_view(), name='update_realty'),
    path('delete_realty/<slug:realty_slug>/', views.DeleteRealtyView.as_view(), name='delete_realty'),

    # CRUD пользователей
    path('update_user_data/<int:pk>/', views.UpdateUserView.as_view(), name='update_user_data'),
    path('delete_user/<int:user_id>/', views.DeleteUserView.as_view(), name='delete_user'),
    path('profile/<int:pk>/', views.UpdateUserView.as_view(), name='profile_user'),

    # Запросы (Query)
    # path('query/', views.UserQueryListView.as_view(), name='query'),
    path('query/new/<slug:realty_slug>/', views.QueryManagementView.as_view(), name='create_query'),  # POST
    path('query/delete/<int:query_id>/', views.QueryManagementView.as_view(), name='delete_query'),   # DELETE
    path('query/accept/<int:query_id>/', views.QueryManagementView.as_view(), name='accept_query'),   # PUT

    # Покупка и Stripe
    path('buy_realty/<slug:realty_slug>/', views.PaymentView.as_view(), name='buy_realty'),           # GET (форма), POST (stripe)
    path('success/<slug:realty_slug>/<int:landlord_id>/', views.PaymentView.as_view(), name='success'), # PUT
    path('cancel/', views.cancel, name='cancel'),

    # Отзывы
    path('realty/<slug:realty_slug>/add_review/', views.ReviewView.as_view(), name='add_review'),

    # Админ-статистика
    path('admin_info/', views.AdminManagementView.as_view(), name='admin_info'),

    path('news/', views.NewsView.as_view(), name='news'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
]