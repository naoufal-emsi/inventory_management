from django.contrib import admin
from .models import Produit, Transaction, Profile

admin.site.register(Produit)
admin.site.register(Transaction)
admin.site.register(Profile)

# Register your models here.
