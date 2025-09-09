from django.db import models
from django.utils import timezone

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
    
    