from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django import forms
from decimal import Decimal

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
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
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

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('sale', 'Vente'),
        ('purchase', 'Achat'),
        ('supplier_purchase', 'Supplier Purchase'),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)  # Changed from 10 to 20
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    date = models.DateField(auto_now_add=True)
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions_from', null=True)
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions_to', null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)  # Add this line

    def __str__(self):
        return f"{self.get_type_display()} de {self.quantity} x {self.produit.name}"

    @property
    def total(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Get old transaction if this is an update
        if self.pk:
            old_transaction = Transaction.objects.get(pk=self.pk)
            # Reverse previous balance changes
            self._update_balances(old_transaction, reverse=True)
        
        # Update balances based on transaction type
        self._update_balances(self)
        
        # Update product quantity
        if self.type == 'sale':
            self.produit.quantity -= self.quantity
        else:  # purchase or supplier_purchase
            self.produit.quantity += self.quantity
        self.produit.save()
        
        super().save(*args, **kwargs)

    def _update_balances(self, transaction, reverse=False):
        # Calculate the total amount for the transaction
        total_amount = transaction.price * transaction.quantity
        
        # Apply the multiplier based on whether we're reversing the transaction
        multiplier = -1 if reverse else 1
        
        # Convert to Decimal to avoid type mismatch
        from decimal import Decimal
        amount = Decimal(str(total_amount * multiplier))

        if transaction.type == 'sale':
            # In a sale, from_user receives money, to_user pays
            if transaction.from_user:
                transaction.from_user.balance += amount
                transaction.from_user.save()
            if transaction.to_user:
                transaction.to_user.balance -= amount
                transaction.to_user.save()
        
        elif transaction.type in ['purchase', 'supplier_purchase']:
            # In a purchase, to_user pays, from_user receives
            if transaction.to_user:
                transaction.to_user.balance -= amount
                transaction.to_user.save()
            if transaction.from_user:
                transaction.from_user.balance += amount
                transaction.from_user.save()

    def delete(self, *args, **kwargs):
        # Reverse balance changes before deletion
        self._update_balances(self, reverse=True)
        super().delete(*args, **kwargs)

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

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('unresolved', 'Unresolved'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'user_type': 'staff'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-updated_at']

class TicketResponse(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.ticket.title} by {self.user.username}"
    
    class Meta:
        ordering = ['created_at']

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    user_type = forms.ChoiceField(
        choices=[('staff', 'Staff'), ('supplier', 'Supplier')],
        label='Account Type',
        widget=forms.Select
    )
    first_name = forms.CharField(label='First Name', max_length=150, required=True)
    last_name = forms.CharField(label='Last Name', max_length=150, required=True)
    phone = forms.CharField(label='Phone', max_length=20, required=True)
    address = forms.CharField(label='Address', widget=forms.Textarea, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'first_name', 'last_name', 'phone', 'address')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        if commit:
            user.save()
        return user

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
        fields = ['product', 'quantity']  # Do NOT include 'customer' here

class ProfileUpdateForm(forms.ModelForm):
    profile_pic = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'accept': 'image/*',
        'class': 'hidden-input'
    }))
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_pic']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        
        # Handle profile picture
        if 'profile_pic' in self.files:
            file_data = self.files['profile_pic'].read()
            user.profile_pic = file_data
        
        if commit:
            user.save()
        return user

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['title', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class TicketResponseForm(forms.ModelForm):
    class Meta:
        model = TicketResponse
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }