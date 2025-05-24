from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Produit, Transaction, Supplier, Customer, ActivityLog
from django.contrib.auth.models import User
from .services.inventory_manager import InventoryManager
from .services.manager import Manager
from datetime import datetime
import calendar

inventory_manager = InventoryManager()
report_manager = Manager()

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return render(request, 'signup.html')

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
    total_products = Produit.objects.count()
    low_stock_count = Produit.objects.filter(quantity__lte=10).count()
    total_value = sum(p.price * p.quantity for p in Produit.objects.all())
    recent_transactions = Transaction.objects.all().order_by('-date')[:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_value': total_value,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)

@login_required
def inventory(request):
    products = inventory_manager.list_all_products()
    return render(request, 'inventory.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        data = {
            'name': request.POST['name'],
            'category': request.POST['category'],
            'price': float(request.POST['price']),
            'quantity': int(request.POST['quantity']),
        }
        inventory_manager.add_product(data)
        messages.success(request, 'Product added successfully')
        return redirect('inventory')
    return redirect('inventory')

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Produit, id=product_id)
    if request.method == 'POST':
        data = {
            'name': request.POST['name'],
            'category': request.POST['category'],
            'price': float(request.POST['price']),
            'quantity': int(request.POST['quantity']),
        }
        inventory_manager.update_product(product_id, data)
        messages.success(request, 'Product updated successfully')
        return redirect('inventory')
    return render(request, 'edit_product.html', {'product': product})

@login_required
def delete_product(request, product_id):
    if request.method == 'POST':
        inventory_manager.delete_product(product_id)
        messages.success(request, 'Product deleted successfully')
    return redirect('inventory')

@login_required
def transactions(request):
    products = Produit.objects.all()
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'transactions.html', {
        'products': products,
        'transactions': transactions
    })

@login_required
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
            messages.success(request, 'Sale recorded successfully')
        else:
            messages.error(request, 'Insufficient stock')
    return redirect('transactions')

@login_required
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
        messages.success(request, 'Purchase recorded successfully')
    return redirect('transactions')

@login_required
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
def settings_view(request):
    return render(request, 'settings.html')

@login_required
def suppliers(request):
    suppliers = Supplier.objects.all()
    return render(request, 'suppliers.html', {'suppliers': suppliers})

@login_required
def customers(request):
    customers = Customer.objects.all()
    return render(request, 'customers.html', {'customers': customers})

@login_required
def activity_log(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')[:100]
    return render(request, 'activity_log.html', {'logs': logs})

@login_required
def analytics(request):
    # Dummy analytics data for now
    data = {
        'total_users': User.objects.count(),
        'total_suppliers': Supplier.objects.count(),
        'total_customers': Customer.objects.count(),
    }
    return render(request, 'analytics.html', data)

@login_required
def support(request):
    return render(request, 'support.html')