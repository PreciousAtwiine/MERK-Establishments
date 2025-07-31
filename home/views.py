from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User

# Create your views here.

class Login(LoginView):
    form_class = LoginForm #This uses the Login Form created in forms.py
    template_name = 'login.html' #This is the template that will be used to render the login form
    
    def get_success_url(self):
        #redirect to the view_sales page after successful login
        return reverse_lazy('home:/sales')
        #return '/view/'
    
    def dispatch(self,request, *args, **kwargs):
        #This method is used to handle the request and return the response
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)
    
    def form_invalid(self,form):
        #This method is used to handle the case when the form is invalid
        messages.error(self.request, 'Invalid username or password.')
        return redirect(reverse_lazy('home:signup'))
    

def signup(request):
    if request.user.is_authenticated:
        return redirect('/sales/')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully!')
            
            
            return redirect('/sales/')
        else:
            messages.error(request, 'Error creating account. Please try again.')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

#Add sales view
@login_required
def add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale added successfully!')
            #return '/view_sales/'  # Redirect to the view_sales page after successful sale addition
            return redirect('/view_sales/')
    else:
        form = SaleForm()
    return render(request, 'add_sale.html',{'form':form})

#View sales
@login_required
def view_sales(request):
    sales = Sale.objects.all().select_related('product_name')
    total_sales = sum(sale.unit_price * sale.quantity for sale in sales)
    context = {
        'sales': sales,
        'total_sales': total_sales,
    }
    return render(request, 'view_sales.html', context)

def products(request):
    products = Stock.objects.all()
    context = {
        'products': products,
    }
    return render(request, 'products.html', context)

@login_required
def add_product(request):
    if request.method=='POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('/products/')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})
            
        
            
        
        
