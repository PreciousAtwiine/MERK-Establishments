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
    path('sales/',views.view_sales,name='view_sales'),
    path('signup/',views.signup,name='signup'),
    path('products/', views.products, name='products'),
    path('products/add/', views.add_product, name='add_product'),
]