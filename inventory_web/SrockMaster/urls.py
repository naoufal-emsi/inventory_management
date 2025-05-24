# SrockMaster/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('inventaire/', views.inventaire_view, name='inventaire'),
]
