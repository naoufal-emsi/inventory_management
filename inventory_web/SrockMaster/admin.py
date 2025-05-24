from django.contrib import admin
from .models import Produit, Transaction, Profile, Supplier, Customer, ActivityLog

admin.site.register(Produit)
admin.site.register(Transaction)
admin.site.register(Profile)
admin.site.register(Supplier)
admin.site.register(Customer)
admin.site.register(ActivityLog)

# Register your models here.
