from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import (
    Produit, Transaction, ActivityLog, CustomUser, SupplierProfile, 
    StaffProfile, Customer, Purchase, CustomUserCreationForm, 
    CustomerForm, PurchaseForm
)
from .services.inventory_manager import InventoryManager
from .services.manager import Manager
from datetime import datetime
import calendar

inventory_manager = InventoryManager()
report_manager = Manager()

def is_admin(user):
    return user.is_admin_user()

def is_supplier(user):
    return user.is_supplier_user()

def is_staff_user(user):
    return user.is_staff_user()

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.user_type == 'supplier':
                SupplierProfile.objects.create(user=user)
            elif user.user_type == 'staff':
                StaffProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if is_supplier(request.user):
        products = Produit.objects.filter(supplier=request.user)
        total_products = products.count()
        total_value = sum(p.price * p.quantity for p in products)
        recent_transactions = Transaction.objects.filter(
            produit__supplier=request.user
        ).order_by('-date')[:5]
    else:
        total_products = Produit.objects.count()
        total_value = sum(p.price * p.quantity for p in Produit.objects.all())
        recent_transactions = Transaction.objects.all().order_by('-date')[:5]

    low_stock_count = Produit.objects.filter(quantity__lte=10).count()

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_value': total_value,
        'recent_transactions': recent_transactions,
        'user_type': request.user.user_type,
    }
    return render(request, 'dashboard.html', context)

@login_required
@user_passes_test(lambda u: not is_supplier(u))
def inventory(request):
    products = inventory_manager.list_all_products()
    return render(request, 'inventory.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        data = {
            'name': request.POST['name'],
            'description': request.POST.get('description', ''),
            'category': request.POST['category'],
            'price': float(request.POST['price']),
            'quantity': int(request.POST['quantity']),
            'supplier': request.user if is_supplier(request.user) else None,
            'status': 'offered' if is_supplier(request.user) else 'approved',
        }
        product = inventory_manager.add_product(data)
        messages.success(request, 'Product added successfully')
        return redirect('inventory' if not is_supplier(request.user) else 'suppliers')
    return redirect('inventory')

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Produit, id=product_id)
    
    if is_supplier(request.user) and product.supplier != request.user:
        return HttpResponseForbidden()
        
    if request.method == 'POST':
        data = {
            'name': request.POST['name'],
            'description': request.POST.get('description', ''),
            'category': request.POST['category'],
            'price': float(request.POST['price']),
            'quantity': int(request.POST['quantity']),
        }
        inventory_manager.update_product(product_id, data)
        messages.success(request, 'Product updated successfully')
        return redirect('inventory' if not is_supplier(request.user) else 'suppliers')
    return render(request, 'edit_product.html', {'product': product})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Produit, id=product_id)
    
    if is_supplier(request.user) and product.supplier != request.user:
        return HttpResponseForbidden()
        
    if request.method == 'POST':
        inventory_manager.delete_product(product_id)
        messages.success(request, 'Product deleted successfully')
    return redirect('inventory' if not is_supplier(request.user) else 'suppliers')

@login_required
@user_passes_test(lambda u: not is_supplier(u))
def transactions(request):
    products = Produit.objects.all()
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'transactions.html', {
        'products': products,
        'transactions': transactions
    })

@login_required
@user_passes_test(lambda u: not is_supplier(u))
def record_sale(request):
    if request.method == 'POST':
        product_id = int(request.POST['product'])
        quantity = int(request.POST['quantity'])
        product = get_object_or_404(Produit, id=product_id)
        
        if product.quantity >= quantity:
            Transaction.objects.create(
                produit=product,
                type='sale',
                quantity=quantity,
                price=product.price
            )
            product.quantity -= quantity
            product.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='Sale recorded',
                details=f'Sold {quantity} units of {product.name}'
            )
            
            messages.success(request, 'Sale recorded successfully')
        else:
            messages.error(request, 'Insufficient stock')
    return redirect('transactions')

@login_required
@user_passes_test(lambda u: not is_supplier(u))
def record_purchase(request):
    if request.method == 'POST':
        product_id = int(request.POST['product'])
        quantity = int(request.POST['quantity'])
        price = float(request.POST['price'])
        product = get_object_or_404(Produit, id=product_id)
        
        Transaction.objects.create(
            produit=product,
            type='purchase',
            quantity=quantity,
            price=price
        )
        product.quantity += quantity
        product.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action='Purchase recorded',
            details=f'Purchased {quantity} units of {product.name}'
        )
        
        messages.success(request, 'Purchase recorded successfully')
    return redirect('transactions')

@login_required
@user_passes_test(lambda u: not is_supplier(u))
def reports(request):
    current_date = datetime.now()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = range(current_date.year - 2, current_date.year + 1)

    monthly_report = report_manager.generate_monthly_report(selected_month, selected_year)
    monthly_report['month_name'] = calendar.month_name[selected_month]
    monthly_report['year'] = selected_year

    top_selling = report_manager.get_top_selling_products()
    low_stock = Produit.objects.filter(quantity__lte=10)

    context = {
        'monthly_report': monthly_report,
        'top_selling': top_selling,
        'low_stock': low_stock,
        'months': months,
        'years': years,
        'selected_month': selected_month,
        'selected_year': selected_year,
    }
    return render(request, 'reports.html', context)

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
@user_passes_test(is_admin)
def settings_view(request):
    return render(request, 'settings.html')

@login_required
def suppliers(request):
    context = {
        'is_supplier': is_supplier(request.user),
        'is_admin': is_admin(request.user),
    }
    
    if is_supplier(request.user):
        # Supplier viewing their own products
        context['products'] = Produit.objects.filter(supplier=request.user)
    elif is_admin(request.user):
        # Admin viewing all supplier products
        context['suppliers'] = SupplierProfile.objects.all()
        context['offered_products'] = Produit.objects.filter(status='offered')
    else:
        return HttpResponseForbidden()
        
    return render(request, 'suppliers.html', context)

@login_required
@user_passes_test(lambda u: not is_supplier(u))
def customers(request):
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST)
        purchase_form = PurchaseForm(request.POST)
        if customer_form.is_valid() and purchase_form.is_valid():
            customer = customer_form.save()
            purchase = purchase_form.save(commit=False)
            purchase.customer = customer
            purchase.added_by = request.user
            purchase.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='Customer and purchase added',
                details=f'Added customer {customer.name} and recorded purchase'
            )
            
            messages.success(request, 'Customer and purchase recorded!')
            return redirect('customers')
    else:
        customer_form = CustomerForm()
        purchase_form = PurchaseForm()
    
    customers = Customer.objects.all()
    purchases = Purchase.objects.select_related('customer', 'product').all().order_by('-date')
    return render(request, 'customers.html', {
        'customers': customers,
        'purchases': purchases,
        'customer_form': customer_form,
        'purchase_form': purchase_form,
    })

@login_required
@user_passes_test(is_admin)
def activity_log(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')[:100]
    return render(request, 'activity_log.html', {'logs': logs})

@login_required
@user_passes_test(is_admin)
def analytics(request):
    data = {
        'total_users': CustomUser.objects.count(),
        'total_suppliers': SupplierProfile.objects.count(),
        'total_customers': Customer.objects.count(),
    }
    return render(request, 'analytics.html', data)

@login_required
def support(request):
    return render(request, 'support.html')

@login_required
@user_passes_test(is_admin)
def approve_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Produit, id=product_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            product.status = 'approved'
            messages.success(request, f'Product "{product.name}" has been approved')
        elif action == 'reject':
            product.status = 'rejected'
            messages.success(request, f'Product "{product.name}" has been rejected')
            
        product.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f'Product {action}d',
            details=f'{action.title()}d product: {product.name}'
        )
        
    return redirect('suppliers')