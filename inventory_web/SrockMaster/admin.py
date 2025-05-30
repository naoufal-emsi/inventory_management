from django.contrib import admin
from .models import Produit, Transaction, CustomUser, SupplierProfile, StaffProfile, ActivityLog, Customer, Purchase
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Balance Information', {'fields': ('balance',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Balance Information', {'fields': ('balance',)}),
    )

admin.site.register(Produit)
admin.site.register(Transaction)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SupplierProfile)
admin.site.register(StaffProfile)
admin.site.register(ActivityLog)
admin.site.register(Customer)
admin.site.register(Purchase)