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

from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy

class Login(LoginView):
    form_class = LoginForm
    template_name = 'index.html'

    def get_success_url(self):
        return reverse_lazy('home:view_sales')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        # Re-render the login page with form errors instead of redirecting to signup
        return self.render_to_response(self.get_context_data(form=form))

# class Login(LoginView):
#     form_class = LoginForm
#     template_name = 'index.html'
    
#     def get_success_url(self):
#         # redirect to the named route for sales
#         return reverse_lazy('home:view_sales')
#         #return '/view/'
    
#     def dispatch(self,request, *args, **kwargs):
#         #This method is used to handle the request and return the response
#         if request.user.is_authenticated:
#             return redirect(self.get_success_url())
#         return super().dispatch(request, *args, **kwargs)
    
#     def form_invalid(self,form):
#         #This method is used to handle the case when the form is invalid
#         messages.error(self.request, 'Invalid username or password.')
#         return redirect(reverse_lazy('home:signup'))
    

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
    product_count = Stock.objects.count()
    todays_sales = Sale.objects.filter(date=timezone.now().date()).count()
    todays_products = Stock.objects.filter(date=timezone.now().date()).count()
    context = {
        'sales': sales,
        'total_sales': total_sales,
        'product_count': product_count,
        'todays_sales': todays_sales,
        'todays_products': todays_products,
    }
    return render(request, 'view_sales.html', context)

@login_required
def products(request):
    products = Stock.objects.all()
    product_count = products.count()
    todays_sales = Sale.objects.filter(date=timezone.now().date()).count()
    todays_products = Stock.objects.filter(date=timezone.now().date()).count()
    context = {
        'products': products,
        'product_count': product_count,
        'todays_sales': todays_sales,
        'todays_products': todays_products,
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

@login_required
def users_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'users.html', {'users': users})

@login_required
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('home:users_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'edit_user.html', {'form': form, 'user_obj': user})

@login_required
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if request.user.pk == user.pk:
            messages.error(request, "You can't delete your own account while signed in.")
        else:
            user.delete()
            messages.success(request, 'User deleted successfully!')
    return redirect('home:users_list')

@login_required
def profile_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    # Ensure a profile exists
    profile, _ = getattr(target_user, 'profile', None), None
    if profile is None:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=target_user)

    can_edit = request.user.is_staff or request.user.pk == target_user.pk
    if request.method == 'POST' and can_edit:
        user_form = UserUpdateForm(request.POST, instance=target_user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('home:profile', pk=target_user.pk)
    else:
        user_form = UserUpdateForm(instance=target_user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {
        'target_user': target_user,
        'user_form': user_form,
        'profile_form': profile_form,
        'can_edit': can_edit,
    })
