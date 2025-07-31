from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.models import User
#Accessing ModelForm from django
from django.forms import ModelForm
#accessing our models to create corresponding forms
#Importing all forms
from .models import *

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product_name', 'unit_price', 'quantity', 'sales_agent', 'customer_name', 'organization', 'customer_phonenumber', 'payment_method']
        def __int__(self, *args,**kwargs):
            super().__init__(*args,**kwargs)
            # only show products that have stock available
            self.fields['product_name'].queryset = Stock.objects.filter(quantity__gt=0)
            def clean_quantity(self):
                quantity = self.cleaned_data['quantity']
                product = self.cleaned_data.get('product')
        
                if product and quantity > product.stock_quantity:
                    raise forms.ValidationError(
                        f"Only {product.stock_quantity} items available in stock."
            )
                return quantity
            
class LoginForm(AuthenticationForm):  
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)   
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Login', css_class='btn btn-primary'))
        
        remember_me = forms.BooleanField(required=False, label = "Remember me")       
                
                
class ProductForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product_name', 'product_description', 'unit_cost', 'unit_price', 'quantity', 'product_supplier']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_description': forms.Textarea(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'product_supplier': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_method = 'post'
            self.helper.add_input(Submit('submit', 'Sign Up', css_class='btn btn-primary btn-block'))