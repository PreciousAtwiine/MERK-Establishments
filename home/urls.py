from django.urls import path
from . import views
from home import views
app_name = 'home'
#borrowing the functionality of login from django
from django.contrib.auth import views as auth_views
urlpatterns = [
    #path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('',views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/',auth_views.LogoutView.as_view(template_name='logout.html'),name='logout'),
    path('sales/add/',views.add_sale, name='add_sale'),
    path('sales/<int:pk>/edit/', views.edit_sale, name='edit_sale'),
    path('sales/<int:pk>/delete/', views.delete_sale, name='delete_sale'),
    path('sales/',views.view_sales,name='view_sales'),
    path('signup/',views.signup,name='signup'),
    path('products/', views.products, name='products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('auth/request-code/', views.request_login_code, name='request_code'),
    path('auth/verify-code/', views.verify_login_code, name='verify_code'),
    path('auth/set-password/', views.set_new_password, name='set_new_password'),
    path('users/', views.users_list, name='users_list'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:pk>/profile/', views.profile_view, name='profile'),
]