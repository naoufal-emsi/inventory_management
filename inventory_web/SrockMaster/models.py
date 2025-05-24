from django.db import models
from django.contrib.auth.models import User

class Produit(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    quantity = models.IntegerField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.quantity} unités"

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('sale', 'Vente'),
        ('purchase', 'Achat'),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} de {self.quantity} x {self.produit.name}"

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Manager'),
        ('staff', 'Employé'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
