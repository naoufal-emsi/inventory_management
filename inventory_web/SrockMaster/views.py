from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Produit, Transaction, ActivityLog, CustomUser, SupplierProfile, StaffProfile, Customer, Purchase, CustomUserCreationForm, CustomerForm, PurchaseForm, ProfileUpdateForm
from .services.inventory_manager import InventoryManager
from .services.manager import Manager
from datetime import datetime
import calendar
from django.db.models import Q
import base64

inventory_manager = InventoryManager()
report_manager = Manager()

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = request.POST.get('user_type', 'staff')
            if user.user_type == 'supplier':
                user.contact = request.POST.get('contact', '')
                user.phone = request.POST.get('phone', '')
                user.address = request.POST.get('address', '')
            user.save()
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
    if request.user.user_type == 'supplier':
        products = Produit.objects.filter(supplier=request.user)
    else:
        products = Produit.objects.all()

    total_products = products.count()
    low_stock_count = products.filter(quantity__lte=10).count()
    total_value = sum(p.price * p.quantity for p in products)
    recent_transactions = Transaction.objects.filter(produit__in=products).order_by('-date')[:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_value': total_value,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)

@login_required
def inventory(request):
    if request.user.user_type == 'supplier':
        products = inventory_manager.list_all_products().filter(supplier=request.user)
    else:
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
            'supplier': request.user if request.user.user_type == 'supplier' else None,
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
    if request.user.user_type == 'supplier':
        products = Produit.objects.filter(supplier=request.user)
        transactions = Transaction.objects.filter(produit__in=products).order_by('-date')
    else:
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
            unit_price = product.price
            Transaction.objects.create(
                produit=product,
                type='sale',
                quantity=quantity,
                price=unit_price
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
        product = get_object_or_404(Produit, id=product_id)
        unit_price = product.price
        Transaction.objects.create(
            produit=product,
            type='purchase',
            quantity=quantity,
            price=unit_price
        )
        product.quantity += quantity
        product.save()
        messages.success(request, 'Purchase recorded successfully')
    return redirect('transactions')

@login_required
def reports(request):
    if request.user.user_type == 'supplier':
        products = Produit.objects.filter(supplier=request.user)
        transactions = Transaction.objects.filter(produit__in=products)
    else:
        products = Produit.objects.all()
        transactions = Transaction.objects.all()

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
    user = request.user
    profile_pic_b64 = None
    if user.profile_pic:
        profile_pic_b64 = base64.b64encode(user.profile_pic).decode('utf-8')
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # No need to handle profile_pic here; handled in form.save()
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, 'profile.html', {'form': form, 'user': user, 'profile_pic_b64': profile_pic_b64})

@login_required
def settings_view(request):
    return render(request, 'settings.html')

@login_required
def suppliers(request):
    suppliers = CustomUser.objects.filter(Q(user_type='supplier'))
    return render(request, 'suppliers.html', {'suppliers': suppliers})

@login_required
def customers(request):
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST)
        purchase_form = PurchaseForm(request.POST)
        if customer_form.is_valid() and purchase_form.is_valid():
            # Save customer first
            customer = customer_form.save()
            # Prepare purchase but don't save yet
            purchase = purchase_form.save(commit=False)
            purchase.customer = customer
            purchase.added_by = request.user
            purchase.price = purchase.product.price * purchase.quantity
            product = purchase.product
            if product.quantity >= purchase.quantity:
                product.quantity -= purchase.quantity
                product.save()
                purchase.save()
                messages.success(request, 'Customer and purchase recorded!')
                return redirect('customers')
            else:
                messages.error(request, 'Insufficient stock for this purchase.')
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
def activity_log(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        details = request.POST.get('details', '')
        ActivityLog.objects.create(user=request.user, action=action, details=details)
        messages.success(request, 'Activity logged successfully!')
        return redirect('activity_log')

    logs = ActivityLog.objects.all().order_by('-timestamp')[:100]
    return render(request, 'activity_log.html', {'logs': logs})

@login_required
def analytics(request):
    data = {
        'total_users': CustomUser.objects.count(),
        'total_suppliers': SupplierProfile.objects.count(),
        'total_customers': 0,  # No Customer model
    }
    return render(request, 'analytics.html', data)

@login_required
def support(request):
    return render(request, 'support.html')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def supplier_products(request, supplier_id):
    supplier = get_object_or_404(CustomUser, id=supplier_id, user_type='supplier')
    products = Produit.objects.filter(supplier=supplier)
    return render(request, 'supplier_products.html', {'supplier': supplier, 'products': products})