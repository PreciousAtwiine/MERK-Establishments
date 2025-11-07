from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

#Reset password
class PasswordResetCode(models.Model):
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self) -> bool:
        return (not self.used) and timezone.now() < self.expires_at

    def __str__(self) -> str:
        return f"ResetCode(email={self.email}, used={self.used})"


class Stock(models.Model):
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(null=False,blank=False)
    unit_cost = models.FloatField(default=0)
    unit_price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    product_supplier = models.TextField(max_length=100)
    date = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.product_name
class Sale(models.Model):
    product_name = models.ForeignKey(Stock,on_delete=models.CASCADE,null=False,blank=False)
    unit_price= models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    sales_agent=models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    organization= models.CharField(max_length=100,blank=True)
    customer_phonenumber= models.CharField(max_length=14,blank=True)
    payment_method = models.CharField(choices=[('Cash','Cash'),('Mpesa','Mpesa'),('Bank','Bank')],max_length=10, default='Cash')
    date= models.DateField(auto_now_add=True)
    def __str__(self):
        return f"{self.product_name} - {self.quantity} units sold by {self.sales_agent} on {self.date}"
    
class Staff(models.Model):
    first_name = models.CharField(max_length=100 , blank= False, null= False)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=14,unique = True, blank = False)
    nin = models.CharField(max_length= 20, unique = True, blank=False, null=False)
    department = models.CharField(max_length = 100, blank = False, null=False)
    
    def __str__(self):
        return self.first_name + " " + self.last_name
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Save profile images directly into the app's static folder so they can be
    # served via STATIC_URL. This uses a FileSystemStorage pointed at
    # <BASE_DIR>/home/static/profile_pictures and sets the URL base to
    # /static/profile_pictures/ so avatar.url resolves correctly.
    _profile_pictures_dir = os.path.join(settings.BASE_DIR, 'home', 'static', 'profile_pictures')
    try:
        os.makedirs(_profile_pictures_dir, exist_ok=True)
    except Exception:
        pass

    profile_pictures_storage = FileSystemStorage(
        location=_profile_pictures_dir,
        base_url=settings.STATIC_URL.rstrip('/') + '/profile_pictures/'
    )

    avatar = models.ImageField(upload_to='', storage=profile_pictures_storage, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"