from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django import forms

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('supplier', 'Supplier'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='staff')
    contact = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_pic = models.BinaryField(blank=True, null=True, editable=True)
    # You can add more fields if needed

class Produit(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    quantity = models.IntegerField()
    category = models.CharField(max_length=50)
    supplier = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, limit_choices_to={'user_type': 'supplier'}, related_name='products')

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

    @property
    def total(self):
        return self.price * self.quantity

class SupplierProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.company_name or self.user.username

class StaffProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff_profile')
    phone = models.CharField(max_length=20, blank=True)
    # Add more staff-specific fields if needed

    def __str__(self):
        return self.user.username

class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    user_type = forms.ChoiceField(
        choices=[('staff', 'Staff'), ('supplier', 'Supplier')],
        label='Account Type',
        widget=forms.Select
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.customer.name} bought {self.quantity} x {self.product.name}"

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['customer', 'product', 'quantity', 'price']

class ProfileUpdateForm(forms.ModelForm):
    profile_pic = forms.ImageField(required=False)
    password = forms.CharField(label='New Password', widget=forms.PasswordInput, required=False)
    email = forms.EmailField(disabled=True)
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Handle profile_pic as binary data
        profile_pic_file = self.files.get('profile_pic')
        if profile_pic_file:
            user.profile_pic = profile_pic_file.read()
        if commit:
            user.save()
        return user
