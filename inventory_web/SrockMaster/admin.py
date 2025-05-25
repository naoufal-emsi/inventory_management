from django.contrib import admin
from .models import Produit, Transaction, CustomUser, SupplierProfile, StaffProfile, ActivityLog
from django.contrib.auth.admin import UserAdmin

admin.site.register(Produit)
admin.site.register(Transaction)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(SupplierProfile)
admin.site.register(StaffProfile)
admin.site.register(ActivityLog)

# Register your models here.
