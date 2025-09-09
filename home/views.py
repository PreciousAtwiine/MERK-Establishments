from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import PasswordResetCode
from django.shortcuts import get_object_or_404

# Create your views here.

class Login(LoginView):
    form_class = LoginForm #This uses the Login Form created in forms.py
    template_name = 'login.html' #This is the template that will be used to render the login form
    
    def get_success_url(self):
        # redirect to the named route for sales
        return reverse_lazy('home:view_sales')
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
            return redirect('home:view_sales')
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
            # Redirect to the view_sales page after successful sale addition
            return redirect('home:view_sales')
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

@login_required
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
            
@login_required
def edit_product(request, pk):
    product = get_object_or_404(Stock, pk=pk)
    if request.method=='POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('home:products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'add_product.html', {'form': form})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    return redirect('home:products')

# Passwordless code flow

def request_login_code(request):
    if request.method == 'POST':
        form = RequestLoginCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = get_random_string(6, allowed_chars='0123456789')
            expires_at = timezone.now() + timezone.timedelta(minutes=5)
            PasswordResetCode.objects.create(email=email, code=code, expires_at=expires_at)
            send_mail(
                subject='Your MERK one-time code',
                message=f'Your one-time login code is: {code}\nIt expires in 5 minutes.',
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )
            messages.success(request, 'We sent a code to your email. Enter it below to continue.')
            verify_form = VerifyLoginCodeForm(initial={'email': email})
            # Pass remaining seconds to expiry (5 minutes = 300 seconds)
            return render(request, 'verify_code.html', {
                'form': verify_form,
                'expires_in_seconds': 300,
            })
    else:
        form = RequestLoginCodeForm()
    return render(request, 'request_code.html', {'form': form})


def verify_login_code(request):
    if request.method == 'POST':
        form = VerifyLoginCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = form.cleaned_data['code']
            record = PasswordResetCode.objects.filter(email__iexact=email, code=code).order_by('-created_at').first()
            if record and record.is_valid():
                record.used = True
                record.save(update_fields=['used'])
                # Store email in session and redirect to set password
                request.session['reset_email'] = email
                messages.success(request, 'Code verified. Set your new password.')
                return redirect('home:set_new_password')
            messages.error(request, 'Invalid or expired code.')
            return render(request, 'verify_code.html', {'form': form})
    return redirect('home:login')
            
@login_required
def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale updated successfully!')
            return redirect('home:view_sales')
    else:
        form = SaleForm(instance=sale)
    return render(request, 'add_sale.html',{'form':form})

@login_required
def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale deleted successfully!')
    return redirect('home:view_sales')


def set_new_password(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please request a new code.')
        return redirect('home:request_code')
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, 'Account not found.')
        return redirect('home:request_code')
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.save()
            # Clear the session key
            request.session.pop('reset_email', None)
            auth_login(request, user)
            messages.success(request, 'Password updated. You are now signed in.')
            return redirect('home:view_sales')
    else:
        form = SetNewPasswordForm()
    return render(request, 'set_password.html', {'form': form})

        
            
        
        
