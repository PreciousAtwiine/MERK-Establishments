from functools import wraps

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import F, FloatField, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import *
from .models import *
from .models import PasswordResetCode


def staff_required(view):
    """Allow only signed-in staff users. Everyone else gets 403 Forbidden."""
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


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


def signup(request):
    if request.user.is_authenticated:
        return redirect('home:view_sales')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # The new account isn't signed in automatically, so send the user to sign in.
            messages.success(request, 'Account created. Sign in to continue.')
            return redirect('home:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


# ---------------------------------------------------------------- Sales

@login_required
def add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale added successfully!')
            return redirect('home:view_sales')
    else:
        form = SaleForm()
    return render(request, 'add_sale.html', {'form': form, 'is_edit': False})


@login_required
def view_sales(request):
    today = timezone.now().date()
    sales = Sale.objects.all().select_related('product_name').order_by('-date', '-id')
    total_sales = sum(sale.unit_price * sale.quantity for sale in sales)
    product_count = Stock.objects.count()
    todays_sales = Sale.objects.filter(date=today).count()
    todays_products = Stock.objects.filter(date=today).count()
    todays_value = (
        Sale.objects.filter(date=today)
        .aggregate(v=Sum(F('unit_price') * F('quantity'), output_field=FloatField()))['v'] or 0
    )
    units_in_stock = Stock.objects.aggregate(q=Sum('quantity'))['q'] or 0
    out_of_stock = Stock.objects.filter(quantity__lte=0).count()
    context = {
        'sales': sales,
        'total_sales': total_sales,
        'product_count': product_count,
        'todays_sales': todays_sales,
        'todays_products': todays_products,
        'todays_value': todays_value,
        'units_in_stock': units_in_stock,
        'out_of_stock': out_of_stock,
    }
    return render(request, 'view_sales.html', context)


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
    return render(request, 'add_sale.html', {'form': form, 'is_edit': True, 'sale': sale})


@login_required
def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale deleted successfully!')
    return redirect('home:view_sales')


# ---------------------------------------------------------------- Products

@login_required
def products(request):
    products = Stock.objects.all().order_by('product_name')
    context = {
        'products': products,
        'product_count': products.count(),
        'todays_sales': Sale.objects.filter(date=timezone.now().date()).count(),
        'todays_products': Stock.objects.filter(date=timezone.now().date()).count(),
    }
    return render(request, 'products.html', context)


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('home:products')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form, 'is_edit': False})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('home:products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'add_product.html', {'form': form, 'is_edit': True, 'product': product})


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    return redirect('home:products')


# ---------------------------------------------------------------- Password reset by emailed code
# Limits use the cache (per process with the default in-memory cache).

CODE_TTL_MINUTES = 5
MAX_CODE_REQUESTS = 3          # per email, per window
REQUEST_WINDOW_SECONDS = 15 * 60
MAX_VERIFY_ATTEMPTS = 5        # wrong codes per email before all its codes are cancelled


def _key(kind, email):
    return f'reset:{kind}:{email.lower()}'


def request_login_code(request):
    if request.method == 'POST':
        form = RequestLoginCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            requests_made = cache.get(_key('requests', email), 0)
            user_exists = User.objects.filter(email__iexact=email).exists()
            if user_exists and requests_made < MAX_CODE_REQUESTS:
                cache.set(_key('requests', email), requests_made + 1, REQUEST_WINDOW_SECONDS)
                cache.delete(_key('attempts', email))
                # Only the newest code is valid.
                PasswordResetCode.objects.filter(email__iexact=email, used=False).update(used=True)
                code = get_random_string(6, allowed_chars='0123456789')
                expires_at = timezone.now() + timezone.timedelta(minutes=CODE_TTL_MINUTES)
                PasswordResetCode.objects.create(email=email, code=code, expires_at=expires_at)
                send_mail(
                    subject='Your MERK one-time code',
                    message=f'Your one-time code is: {code}\nIt expires in {CODE_TTL_MINUTES} minutes.',
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=True,
                )
            # Same response whether or not the account exists or the limit was reached.
            messages.success(request, 'If an account uses that email, we have sent it a 6-digit code.')
            verify_form = VerifyLoginCodeForm(initial={'email': email})
            return render(request, 'verify_code.html', {
                'form': verify_form,
                'email': email,
                'expires_in_seconds': CODE_TTL_MINUTES * 60,
            })
    else:
        form = RequestLoginCodeForm()
    return render(request, 'request_code.html', {'form': form})


def verify_login_code(request):
    if request.method == 'POST':
        form = VerifyLoginCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = form.cleaned_data['code'].strip()
            attempts = cache.get(_key('attempts', email), 0)
            if attempts >= MAX_VERIFY_ATTEMPTS:
                messages.error(request, 'Too many incorrect codes. Request a new code.')
                return redirect('home:request_code')
            record = PasswordResetCode.objects.filter(email__iexact=email, code=code).order_by('-created_at').first()
            if record and record.is_valid():
                record.used = True
                record.save(update_fields=['used'])
                cache.delete(_key('attempts', email))
                request.session['reset_email'] = email
                messages.success(request, 'Code verified. Set your new password.')
                return redirect('home:set_new_password')
            attempts += 1
            cache.set(_key('attempts', email), attempts, CODE_TTL_MINUTES * 60)
            if attempts >= MAX_VERIFY_ATTEMPTS:
                PasswordResetCode.objects.filter(email__iexact=email, used=False).update(used=True)
                messages.error(request, 'Too many incorrect codes. Request a new code.')
                return redirect('home:request_code')
            messages.error(request, 'Invalid or expired code.')
            return render(request, 'verify_code.html', {'form': form, 'email': email})
    return redirect('home:login')


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
            request.session.pop('reset_email', None)
            auth_login(request, user)
            messages.success(request, 'Password updated. You are now signed in.')
            return redirect('home:view_sales')
    else:
        form = SetNewPasswordForm()
    return render(request, 'set_password.html', {'form': form})


# ---------------------------------------------------------------- Users (staff only)

@staff_required
def users_list(request):
    users = User.objects.all().select_related('profile').order_by('username')
    return render(request, 'users.html', {'users': users})


@staff_required
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


@staff_required
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
    # Users can view and edit their own profile; staff can view and edit anyone's.
    if request.user.pk != pk and not request.user.is_staff:
        raise PermissionDenied
    target_user = get_object_or_404(User, pk=pk)
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
