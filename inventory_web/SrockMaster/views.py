from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Sum, F  # Add these imports
from .models import Produit, Transaction, ActivityLog, CustomUser, SupplierProfile, StaffProfile, Customer, Purchase, CustomUserCreationForm, CustomerForm, PurchaseForm, ProfileUpdateForm, SupportTicket, TicketResponse, SupportTicketForm, TicketResponseForm
from .services.inventory_manager import InventoryManager
from .services.manager import Manager
from datetime import datetime
import calendar
from django.db.models import Q
import base64
from django.http import HttpResponse
import csv

inventory_manager = InventoryManager()
report_manager = Manager()

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.user_type = form.cleaned_data['user_type']
                user.save()
                
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').lower()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'login.html')
        
        # Try to get user by email first
        try:
            user = CustomUser.objects.get(email=email)
            username = user.username
        except CustomUser.DoesNotExist:
            # If no user found by email, try username
            username = email
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email/username or password')
    
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
    
    # Get recent balance transactions
    balance_transactions = ActivityLog.objects.filter(
        user=request.user,
        action__contains='balance'
    ).order_by('-timestamp')[:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_value': total_value,
        'recent_transactions': recent_transactions,
        'balance_transactions': balance_transactions,
    }
    return render(request, 'dashboard.html', context)

@login_required
def inventory(request):
    if request.user.user_type == 'supplier':
        # Supplier only sees their own products
        products = inventory_manager.list_all_products().filter(supplier=request.user)
    elif request.user.user_type == 'admin' or request.user.is_superuser:
        # Admin only sees their own products (products with no supplier)
        products = inventory_manager.list_all_products().filter(supplier=None)
    else:
        # Staff sees all products
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
        context = {
            'products': products,
            'transactions': transactions
        }
    else:
        products = Produit.objects.all()
        transactions = Transaction.objects.all().order_by('-date')
        customers = Customer.objects.all()
        context = {
            'products': products,
            'transactions': transactions,
            'customers': customers
        }
    return render(request, 'transactions.html', context)

@login_required
def record_sale(request):
    if request.method == 'POST':
        product_id = int(request.POST['product'])
        quantity = int(request.POST['quantity'])
        customer_id = request.POST.get('customer')  # Add this line
        product = get_object_or_404(Produit, id=product_id)
        
        if product.quantity >= quantity:
            unit_price = product.price
            transaction = Transaction.objects.create(
                produit=product,
                type='sale',
                quantity=quantity,
                price=unit_price
            )
            
            # Add this block
            if customer_id:
                customer = get_object_or_404(Customer, id=customer_id)
                transaction.customer = customer
                transaction.save()
                
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
    # Filter data based on user type
    if request.user.user_type == 'supplier':
        # Get only products owned by this supplier
        products = Produit.objects.filter(supplier=request.user)
        # Get only transactions related to supplier's products
        transactions = Transaction.objects.filter(
            Q(produit__in=products) |  # Transactions of supplier's products
            Q(from_user=request.user) | # Transactions where supplier is seller
            Q(to_user=request.user)     # Transactions where supplier is buyer
        )
    else:
        # Admin/staff can see all data
        products = Produit.objects.all()
        transactions = Transaction.objects.all()

    current_date = datetime.now()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = range(current_date.year - 2, current_date.year + 1)

    # Calculate financial metrics for filtered data
    financial_metrics = report_manager.calculate_financial_metrics_for_supplier(
        request.user if request.user.user_type == 'supplier' else None,
        start_date=datetime(selected_year, selected_month, 1),
        end_date=datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    )

    # Get supplier-specific monthly report
    monthly_report = report_manager.generate_monthly_report_for_supplier(
        selected_month, 
        selected_year,
        supplier=request.user if request.user.user_type == 'supplier' else None
    )

    # Get supplier-specific yearly comparison
    yearly_comparison = report_manager.get_yearly_comparison_for_supplier(
        selected_year,
        supplier=request.user if request.user.user_type == 'supplier' else None
    )

    # Get top selling products for this supplier only
    top_selling = report_manager.get_top_selling_products(
        n=5, 
        supplier=request.user if request.user.user_type == 'supplier' else None
    )

    # Get most profitable products
    most_profitable = report_manager.get_most_profitable_products(
        n=5,
        supplier=request.user if request.user.user_type == 'supplier' else None
    )

    # Get inventory health metrics
    inventory_health = report_manager.get_inventory_health(
        supplier=request.user if request.user.user_type == 'supplier' else None
    )

    # Get customer insights
    customer_insights = report_manager.get_customer_insights(
        supplier=request.user if request.user.user_type == 'supplier' else None
    )

    # Get low stock products for this supplier only
    low_stock = products.filter(quantity__lte=10)

    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="report_{selected_year}_{selected_month}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Report Period', f'{calendar.month_name[selected_month]} {selected_year}'])
        writer.writerow(['Generated for', f'{request.user.get_full_name() or request.user.username} ({request.user.user_type})'])
        writer.writerow([])  # Empty row for spacing
        
        # Write summary
        writer.writerow(['Financial Summary'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Revenue', f"${financial_metrics['summary']['total_revenue']:.2f}"])
        writer.writerow(['Total Expenses', f"${financial_metrics['summary']['total_expenses']:.2f}"])
        writer.writerow(['Gross Profit', f"${financial_metrics['summary']['gross_profit']:.2f}"])
        writer.writerow(['Profit Margin', f"{financial_metrics['summary']['profit_margin']:.2f}%"])
        writer.writerow(['Units Sold', financial_metrics['summary']['units_sold']])
        writer.writerow(['Daily Average Revenue', f"${financial_metrics['summary']['daily_avg_revenue']:.2f}"])
        writer.writerow([])
        
        # Write inventory summary
        writer.writerow(['Inventory Summary'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Inventory Value', f"${financial_metrics['inventory']['total_value']:.2f}"])
        writer.writerow(['Total Items in Stock', financial_metrics['inventory']['total_items']])
        writer.writerow(['Average Product Price', f"${financial_metrics['inventory']['avg_price']:.2f}"])
        writer.writerow(['Low Stock Items', inventory_health['low_stock_count']])
        writer.writerow(['Out of Stock Items', inventory_health['out_of_stock_count']])
        writer.writerow(['Inventory Turnover', f"{inventory_health['inventory_turnover']:.2f}"])
        writer.writerow([])
        
        # Write expense breakdown
        writer.writerow(['Expense Breakdown'])
        writer.writerow(['Type', 'Amount'])
        writer.writerow(['Purchase Expenses', f"${financial_metrics['expense_breakdown']['purchase_expenses']:.2f}"])
        writer.writerow(['Supplier Expenses', f"${financial_metrics['expense_breakdown']['supplier_expenses']:.2f}"])
        writer.writerow([])
        
        # Write category performance
        writer.writerow(['Category Performance'])
        writer.writerow(['Category', 'Revenue', 'Expenses', 'Profit', 'Units Sold', 'Inventory Value'])
        for category, metrics in financial_metrics['category_performance'].items():
            writer.writerow([
                category,
                f"${metrics['revenue']:.2f}",
                f"${metrics['expenses']:.2f}",
                f"${metrics['profit']:.2f}",
                metrics['units_sold'],
                f"${metrics['inventory_value']:.2f}"
            ])
        writer.writerow([])
        
        # Write year-over-year comparison
        writer.writerow(['Year-over-Year Comparison'])
        writer.writerow(['Metric', str(selected_year), str(selected_year-1), 'Growth'])
        writer.writerow([
            'Revenue',
            f"${yearly_comparison['current_year']['summary']['total_revenue']:.2f}",
            f"${yearly_comparison['previous_year']['summary']['total_revenue']:.2f}",
            f"{yearly_comparison['growth']['revenue']:.1f}%"
        ])
        writer.writerow([
            'Profit',
            f"${yearly_comparison['current_year']['summary']['gross_profit']:.2f}",
            f"${yearly_comparison['previous_year']['summary']['gross_profit']:.2f}",
            f"{yearly_comparison['growth']['profit']:.1f}%"
        ])
        writer.writerow([
            'Inventory Value',
            f"${yearly_comparison['current_year']['inventory']['total_value']:.2f}",
            f"${yearly_comparison['previous_year']['inventory']['total_value']:.2f}",
            f"{yearly_comparison['growth']['inventory_value']:.1f}%"
        ])
        writer.writerow([])
        
        # Write top selling products
        writer.writerow(['Top Selling Products'])
        writer.writerow(['Product', 'Category', 'Total Sales', 'Revenue'])
        for product in top_selling:
            writer.writerow([
                product.name,
                product.category,
                product.total_sales,
                f"${product.revenue:.2f}" if product.revenue else "$0.00"
            ])
        writer.writerow([])
        
        # Write most profitable products
        writer.writerow(['Most Profitable Products'])
        writer.writerow(['Product', 'Category', 'Revenue', 'Cost', 'Profit'])
        for product in most_profitable:
            writer.writerow([
                product.name,
                product.category,
                f"${product.revenue:.2f}",
                f"${product.cost:.2f}",
                f"${product.profit:.2f}"
            ])
        writer.writerow([])
        
        # Write customer insights
        writer.writerow(['Customer Insights'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Customers', customer_insights['total_customers']])
        writer.writerow(['Repeat Customers', customer_insights['repeat_customers']])
        writer.writerow(['Customer Retention Rate', f"{customer_insights['retention_rate']:.1f}%"])
        writer.writerow(['Average Purchase Value', f"${customer_insights['average_purchase']:.2f}"])
        
        return response

    context = {
        'monthly_report': monthly_report,
        'yearly_comparison': yearly_comparison,
        'financial_metrics': financial_metrics,
        'top_selling': top_selling,
        'most_profitable': most_profitable,
        'inventory_health': inventory_health,
        'customer_insights': customer_insights,
        'low_stock': low_stock,
        'months': months,
        'years': years,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'user_type': request.user.user_type,
    }
    return render(request, 'reports.html', context)

@login_required
def profile(request):
    user = request.user
    profile_pic_b64 = None
    
    # Get existing profile picture
    if user.profile_pic:
        try:
            profile_pic_b64 = base64.b64encode(user.profile_pic).decode('utf-8')
        except Exception:
            profile_pic_b64 = None

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            
            # After saving, get the updated profile picture
            user.refresh_from_db()
            if user.profile_pic:
                profile_pic_b64 = base64.b64encode(user.profile_pic).decode('utf-8')
            
            # Important: Pass both form and profile_pic_b64 when redirecting
            context = {
                'form': form,
                'user': user,
                'profile_pic_b64': profile_pic_b64
            }
            return render(request, 'profile.html', context)
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'profile.html', {
        'form': form,
        'user': user,
        'profile_pic_b64': profile_pic_b64
    })

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
    # Fetch all customers and all purchases for the tables
    customers = Customer.objects.all()
    purchases = Purchase.objects.select_related('customer', 'product', 'added_by').all().order_by('-date')
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
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete_user':
            user_id = request.POST.get('user_id')
            try:
                user = CustomUser.objects.get(id=user_id)
                if not user.is_superuser:  # Prevent deletion of superusers
                    username = user.username
                    user.delete()
                    messages.success(request, f'User {username} deleted successfully')
                else:
                    messages.error(request, 'Cannot delete superuser accounts')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found')
        
        elif action == 'add_user':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.user_type = request.POST.get('user_type', 'staff')
                user.save()
                messages.success(request, f'User {user.username} created successfully')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
    
    data = {
        'total_users': CustomUser.objects.count(),
        'total_suppliers': CustomUser.objects.filter(user_type='supplier').count(),
        'total_staff': CustomUser.objects.filter(user_type='staff').count(),
        'users': CustomUser.objects.filter(is_superuser=False),  # Add this
        'user_form': CustomUserCreationForm(),  # Add this
    }
    return render(request, 'analytics.html', data)

@login_required
def user_details(request, user_type):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            user = CustomUser.objects.get(id=user_id)
            
            if action == 'delete':
                if not user.is_superuser:
                    username = user.username
                    user.delete()
                    messages.success(request, f'User {username} deleted successfully')
                else:
                    messages.error(request, 'Cannot delete superuser accounts')
                    
            elif action == 'edit':
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.email = request.POST.get('email')
                user.phone = request.POST.get('phone')
                user.address = request.POST.get('address')
                user.user_type = request.POST.get('user_type')
                
                if request.POST.get('new_password'):
                    user.set_password(request.POST.get('new_password'))
                
                user.save()
                messages.success(request, f'User {user.username} updated successfully')
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
    
    if user_type == 'staff':
        users = CustomUser.objects.filter(user_type='staff', is_superuser=False)
        title = "Staff Members"
    elif user_type == 'supplier':
        users = CustomUser.objects.filter(user_type='supplier', is_superuser=False)
        title = "Suppliers"
    else:
        users = CustomUser.objects.filter(is_superuser=False)
        title = "All Users"
    
    return render(request, 'user_details.html', {
        'users': users,
        'title': title,
        'user_types': CustomUser.USER_TYPE_CHOICES
    })

@login_required
def add_funds(request):
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            if amount <= 0:
                messages.error(request, 'Please enter a positive amount.')
                return redirect('profile')
            
            # Update user balance - convert float to Decimal to avoid type mismatch
            from decimal import Decimal
            user = request.user
            user.balance += Decimal(str(amount))
            user.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                action=f'Added ${amount:.2f} to account balance',
                details=f'New balance: ${user.balance:.2f}'
            )
            
            messages.success(request, f'Successfully added ${amount:.2f} to your balance.')
        except ValueError:
            messages.error(request, 'Invalid amount format.')
        except Exception as e:
            messages.error(request, f'Error processing your request: {str(e)}')
    
    return redirect('profile')

@login_required
def set_balance(request):
    if request.method == 'POST':
        try:
            from decimal import Decimal
            new_balance = Decimal(str(request.POST.get('balance', 0)))
            
            if new_balance < 0:
                messages.error(request, 'Balance cannot be negative.')
                return redirect('profile')
                
            user = request.user
            old_balance = user.balance
            user.balance = new_balance
            user.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                action=f'Set account balance to ${new_balance:.2f}',
                details=f'Previous balance: ${old_balance:.2f}'
            )
            
            messages.success(request, f'Successfully set balance to ${new_balance:.2f}.')
        except ValueError:
            messages.error(request, 'Invalid balance format.')
        except Exception as e:
            messages.error(request, f'Error processing your request: {str(e)}')
    
    return redirect('profile')

@login_required
def support(request):
    if request.user.user_type == 'staff' and not request.user.is_superuser:
        # Staff view - show all tickets
        tickets = SupportTicket.objects.all()
        if request.method == 'POST':
            ticket_id = request.POST.get('ticket_id')
            ticket = get_object_or_404(SupportTicket, id=ticket_id)
            form = TicketResponseForm(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.ticket = ticket
                response.user = request.user
                response.save()
                
                # Update ticket status to in_progress
                if ticket.status == 'open' or ticket.status == 'unresolved':
                    ticket.status = 'in_progress'
                    ticket.assigned_to = request.user
                    ticket.save()
                
                messages.success(request, 'Response added successfully')
                return redirect('support')
        else:
            form = TicketResponseForm()
        
        return render(request, 'support_staff.html', {
            'tickets': tickets,
            'form': form
        })
    else:
        # Admin/Supplier view - show own tickets and form to create new ones
        tickets = SupportTicket.objects.filter(created_by=request.user)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'create_ticket':
                form = SupportTicketForm(request.POST)
                if form.is_valid():
                    ticket = form.save(commit=False)
                    ticket.created_by = request.user
                    ticket.save()
                    messages.success(request, 'Support ticket created successfully')
                    return redirect('support')
            
            elif action == 'respond':
                ticket_id = request.POST.get('ticket_id')
                ticket = get_object_or_404(SupportTicket, id=ticket_id, created_by=request.user)
                form = TicketResponseForm(request.POST)
                if form.is_valid():
                    response = form.save(commit=False)
                    response.ticket = ticket
                    response.user = request.user
                    response.save()
                    messages.success(request, 'Response added successfully')
                    return redirect('support')
            
            elif action == 'resolve':
                ticket_id = request.POST.get('ticket_id')
                ticket = get_object_or_404(SupportTicket, id=ticket_id, created_by=request.user)
                ticket.status = 'resolved'
                ticket.save()
                messages.success(request, 'Ticket marked as resolved')
                return redirect('support')
            
            elif action == 'unresolve':
                ticket_id = request.POST.get('ticket_id')
                ticket = get_object_or_404(SupportTicket, id=ticket_id, created_by=request.user)
                ticket.status = 'unresolved'
                ticket.save()
                messages.success(request, 'Ticket marked as unresolved')
                return redirect('support')
        
        form = SupportTicketForm()
        return render(request, 'support.html', {
            'tickets': tickets,
            'form': form
        })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def supplier_products(request, supplier_id):
    supplier = get_object_or_404(CustomUser, id=supplier_id, user_type='supplier')
    products = Produit.objects.filter(supplier=supplier)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('buy_quantity', 0))
        
        if quantity <= 0:
            messages.error(request, 'Please enter a valid quantity.')
            return redirect('supplier_products', supplier_id=supplier_id)
            
        product = get_object_or_404(Produit, id=product_id)
        total_cost = product.price * quantity
        
        # Check if buyer has enough money
        if request.user.balance < total_cost:
            messages.error(request, 'Insufficient funds for this purchase. Please add more funds to your account.')
            return redirect('supplier_products', supplier_id=supplier_id)
            
        # Check if supplier has enough stock
        if product.quantity < quantity:
            messages.error(request, 'Supplier does not have enough stock.')
            return redirect('supplier_products', supplier_id=supplier_id)
            
        try:
            # Start money transfer - convert float to Decimal to avoid type mismatch
            from decimal import Decimal
            decimal_cost = Decimal(str(total_cost))
            
            # Double-check balance is sufficient (in case it changed)
            if request.user.balance < decimal_cost:
                messages.error(request, 'Insufficient funds for this purchase.')
                return redirect('supplier_products', supplier_id=supplier_id)
                
            request.user.balance -= decimal_cost
            supplier.balance += decimal_cost
            
            # Update product quantities for the buyer (admin)
            # First, check if buyer already has this product
            buyer_product = Produit.objects.filter(
                name=product.name,
                supplier=None,
                category=product.category
            ).first()
            
            if buyer_product:
                buyer_product.quantity += quantity
                buyer_product.save()
            else:
                # Create new product entry for buyer
                buyer_product = Produit.objects.create(
                    name=product.name,
                    category=product.category,
                    price=product.price,
                    quantity=quantity,
                    supplier=None
                )
            
            # Reduce supplier's product quantity
            product.quantity -= quantity
            
            # Save all changes
            request.user.save()
            supplier.save()
            product.save()
            
            # Create the transaction record
            transaction = Transaction.objects.create(
                produit=product,
                type='supplier_purchase',
                quantity=quantity,
                price=product.price,
                from_user=supplier,
                to_user=request.user
            )
            
            # Since the transaction.save() already updated balances, we need to fix them
            # by adding back the amount that was deducted (we already did it manually above)
            from decimal import Decimal
            request.user.balance += Decimal(str(total_cost))
            supplier.balance -= Decimal(str(total_cost))
            request.user.save()
            supplier.save()
            
            # The Transaction.save() method incorrectly adds to the supplier's product quantity
            # We need to fix it by subtracting the correct amount
            # Since we want to subtract just 'quantity', but the save method added 'quantity',
            # we need to subtract 2 * quantity to get the correct result
            product.quantity = product.quantity - quantity - quantity  # Correct the quantity
            product.save()
            
            messages.success(request, f'Successfully purchased {quantity} units of {product.name}')
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action=f'Purchased {quantity} {product.name} from supplier {supplier.username}',
                details=f'Total cost: ${total_cost}'
            )
            
        except Exception as e:
            messages.error(request, f'Error processing transaction: {str(e)}')
            
    return render(request, 'supplier_products.html', {'supplier': supplier, 'products': products})