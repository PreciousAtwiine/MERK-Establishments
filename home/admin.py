from django.contrib import admin

# Register your models here.
from .models import *

#Register models here
admin.site.register(Stock)
admin.site.register(Sale)
admin.site.register(Staff)