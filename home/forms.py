from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import *
from .models import Sale, Stock, Profile

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product_name','unit_price','quantity','sales_agent','customer_name','organization','customer_phonenumber','payment_method']
        widgets = {
            'product_name': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'sales_agent': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phonenumber': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative")
        return quantity

class LoginForm(AuthenticationForm):  
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Password'}))
    remember_me = forms.BooleanField(required=False, label = "Remember me")       

class ProductForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product_name','product_description','unit_cost','unit_price','quantity','product_supplier']
        widgets = {
            'product_name': forms.TextInput(attrs={'class':'form-control'}),
            'product_description': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'unit_cost': forms.NumberInput(attrs={'class':'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class':'form-control'}),
            'quantity': forms.NumberInput(attrs={'class':'form-control'}),
            'product_supplier': forms.TextInput(attrs={'class':'form-control'}),
        }

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Sign Up', css_class='btn btn-primary btn-block'))

class RequestLoginCodeForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError("No account found with that email.")
        return email

class VerifyLoginCodeForm(forms.Form):
    email = forms.EmailField()
    code = forms.CharField(max_length=10)

class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(label='New password', widget=forms.PasswordInput(attrs={'class':'form-control'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'class':'form-control'}))

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get('password1')
        pwd2 = cleaned.get('password2')
        if pwd1 and pwd2 and pwd1 != pwd2:
            raise ValidationError("Passwords do not match.")
        if pwd1:
            validate_password(pwd1)
        return cleaned

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control'}),
            'last_name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'phone_number', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class':'form-control'}),
            'bio': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style boolean fields with Bootstrap switches
        self.fields['is_active'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        self.fields['is_staff'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})