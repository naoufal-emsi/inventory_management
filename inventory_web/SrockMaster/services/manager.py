from SrockMaster.models import Transaction, Produit, CustomUser, Customer, Purchase
from collections import Counter
from django.db.models import Sum, F, Q, Count, Avg, Max, Min, Value, DecimalField, FloatField
from django.db.models.functions import TruncMonth, TruncYear, TruncDay, Coalesce
from datetime import datetime, timedelta
from calendar import monthrange
from decimal import Decimal

class Manager:
    def calculate_financial_metrics(self, start_date=None, end_date=None):
        """Calculate detailed financial metrics using real transaction data"""
        if not start_date:
            start_date = datetime.now().replace(day=1)
        if not end_date:
            end_date = datetime.now()

        # Get transactions for the period
        transactions = Transaction.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('produit')

        # Calculate revenue using database aggregation
        sales_metrics = transactions.filter(type='sale').aggregate(
            revenue=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            total_sales=Count('id'),
            avg_sale=Avg(F('price') * F('quantity'), output_field=DecimalField()),
            units_sold=Coalesce(Sum('quantity'), 0)
        )

        # Calculate expenses using database aggregation
        expense_metrics = transactions.filter(
            Q(type='purchase') | Q(type='supplier_purchase')
        ).aggregate(
            total_expenses=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            purchase_expenses=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type='purchase'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            supplier_expenses=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type='supplier_purchase'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            units_purchased=Coalesce(Sum('quantity'), 0)
        )

        # Calculate inventory value
        inventory_value = Produit.objects.aggregate(
            total_value=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            total_items=Coalesce(Sum('quantity'), 0),
            avg_price=Avg('price', output_field=DecimalField()),
            min_price=Min('price'),
            max_price=Max('price')
        )

        # Calculate category performance using database queries
        category_metrics = {}
        categories = Produit.objects.values_list('category', flat=True).distinct()
        
        for category in categories:
            cat_transactions = transactions.filter(produit__category=category)
            cat_products = Produit.objects.filter(category=category)
            
            sales = cat_transactions.filter(type='sale').aggregate(
                revenue=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
                units=Coalesce(Sum('quantity'), 0)
            )
            
            expenses = cat_transactions.filter(
                Q(type='purchase') | Q(type='supplier_purchase')
            ).aggregate(
                expenses=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField()))
            )
            
            inventory = cat_products.aggregate(
                value=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
                items=Coalesce(Sum('quantity'), 0)
            )
            
            category_metrics[category] = {
                'revenue': sales['revenue'],
                'expenses': expenses['expenses'],
                'profit': sales['revenue'] - expenses['expenses'],
                'units_sold': sales['units'],
                'inventory_value': inventory['value'],
                'inventory_items': inventory['items']
            }

        # Calculate actual totals
        total_revenue = sales_metrics['revenue']
        total_expenses = expense_metrics['total_expenses']
        gross_profit = total_revenue - total_expenses

        # Calculate daily sales trend
        daily_sales = transactions.filter(type='sale').annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            revenue=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            units=Sum('quantity')
        ).order_by('day')

        # Calculate customer metrics
        customer_metrics = transactions.filter(
            type='sale', 
            customer__isnull=False
        ).values('customer').annotate(
            total_spent=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            purchases=Count('id')
        ).aggregate(
            avg_customer_value=Avg('total_spent', output_field=DecimalField()),
            total_customers=Count('customer', distinct=True)
        )

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days + 1
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'gross_profit': gross_profit,
                'profit_margin': (gross_profit / total_revenue * 100) if total_revenue > 0 else 0,
                'units_sold': sales_metrics['units_sold'],
                'units_purchased': expense_metrics['units_purchased'],
                'daily_avg_revenue': total_revenue / ((end_date - start_date).days + 1) if (end_date - start_date).days > 0 else total_revenue
            },
            'inventory': {
                'total_value': inventory_value['total_value'],
                'total_items': inventory_value['total_items'],
                'avg_price': inventory_value['avg_price'] or 0,
                'price_range': {
                    'min': inventory_value['min_price'] or 0,
                    'max': inventory_value['max_price'] or 0
                }
            },
            'expense_breakdown': {
                'purchase_expenses': expense_metrics['purchase_expenses'],
                'supplier_expenses': expense_metrics['supplier_expenses']
            },
            'category_performance': category_metrics,
            'transactions_count': sales_metrics['total_sales'],
            'average_transaction_value': sales_metrics['avg_sale'] or 0,
            'daily_trend': list(daily_sales),
            'customer_metrics': {
                'total_customers': customer_metrics['total_customers'] or 0,
                'avg_customer_value': customer_metrics['avg_customer_value'] or 0
            }
        }

    def calculate_financial_metrics_for_supplier(self, supplier=None, start_date=None, end_date=None):
        """Calculate metrics for a specific supplier or all if supplier is None"""
        if not start_date:
            start_date = datetime.now().replace(day=1)
        if not end_date:
            end_date = datetime.now()

        # Get transactions for the period
        transactions = Transaction.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('produit')

        # Add supplier filter if needed
        if supplier:
            transactions = transactions.filter(
                Q(produit__supplier=supplier) |
                Q(from_user=supplier) |
                Q(to_user=supplier)
            )
            products = Produit.objects.filter(supplier=supplier)
        else:
            products = Produit.objects.all()
        
        # Calculate revenue using database aggregation
        sales_metrics = transactions.filter(type='sale').aggregate(
            revenue=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            total_sales=Count('id'),
            avg_sale=Avg(F('price') * F('quantity'), output_field=DecimalField()),
            units_sold=Coalesce(Sum('quantity'), 0)
        )

        # Calculate expenses using database aggregation
        expense_metrics = transactions.filter(
            Q(type='purchase') | Q(type='supplier_purchase')
        ).aggregate(
            total_expenses=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            purchase_expenses=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type='purchase'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            supplier_expenses=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type='supplier_purchase'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            units_purchased=Coalesce(Sum('quantity'), 0)
        )

        # Calculate inventory value
        inventory_value = products.aggregate(
            total_value=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            total_items=Coalesce(Sum('quantity'), 0),
            avg_price=Avg('price', output_field=DecimalField()),
            min_price=Min('price'),
            max_price=Max('price')
        )

        # Calculate category performance using database queries
        category_metrics = {}
        categories = products.values_list('category', flat=True).distinct()
        
        for category in categories:
            cat_transactions = transactions.filter(produit__category=category)
            cat_products = products.filter(category=category)
            
            sales = cat_transactions.filter(type='sale').aggregate(
                revenue=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
                units=Coalesce(Sum('quantity'), 0)
            )
            
            expenses = cat_transactions.filter(
                Q(type='purchase') | Q(type='supplier_purchase')
            ).aggregate(
                expenses=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField()))
            )
            
            inventory = cat_products.aggregate(
                value=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
                items=Coalesce(Sum('quantity'), 0)
            )
            
            category_metrics[category] = {
                'revenue': sales['revenue'],
                'expenses': expenses['expenses'],
                'profit': sales['revenue'] - expenses['expenses'],
                'units_sold': sales['units'],
                'inventory_value': inventory['value'],
                'inventory_items': inventory['items']
            }

        # Calculate actual totals
        total_revenue = sales_metrics['revenue']
        total_expenses = expense_metrics['total_expenses']
        gross_profit = total_revenue - total_expenses

        # Calculate daily sales trend
        daily_sales = transactions.filter(type='sale').annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            revenue=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            units=Sum('quantity')
        ).order_by('day')

        # Calculate customer metrics
        customer_metrics = transactions.filter(
            type='sale', 
            customer__isnull=False
        ).values('customer').annotate(
            total_spent=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            purchases=Count('id')
        ).aggregate(
            avg_customer_value=Avg('total_spent', output_field=DecimalField()),
            total_customers=Count('customer', distinct=True)
        )

        # Calculate supplier-specific metrics if applicable
        supplier_specific = {}
        if supplier:
            # Calculate balance history
            balance_history = supplier.activitylog_set.filter(
                action__contains='balance',
                timestamp__range=[start_date, end_date]
            ).order_by('timestamp')
            
            # Calculate products sold to other users
            products_sold = Transaction.objects.filter(
                from_user=supplier,
                date__range=[start_date, end_date]
            ).aggregate(
                total_sold=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
                units_sold=Coalesce(Sum('quantity'), 0),
                transactions=Count('id')
            )
            
            supplier_specific = {
                'current_balance': supplier.balance,
                'balance_history': list(balance_history.values('timestamp', 'action', 'details')),
                'products_sold_to_others': products_sold
            }

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days + 1
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'gross_profit': gross_profit,
                'profit_margin': (gross_profit / total_revenue * 100) if total_revenue > 0 else 0,
                'units_sold': sales_metrics['units_sold'],
                'units_purchased': expense_metrics['units_purchased'],
                'daily_avg_revenue': total_revenue / ((end_date - start_date).days + 1) if (end_date - start_date).days > 0 else total_revenue
            },
            'inventory': {
                'total_value': inventory_value['total_value'],
                'total_items': inventory_value['total_items'],
                'avg_price': inventory_value['avg_price'] or 0,
                'price_range': {
                    'min': inventory_value['min_price'] or 0,
                    'max': inventory_value['max_price'] or 0
                }
            },
            'expense_breakdown': {
                'purchase_expenses': expense_metrics['purchase_expenses'],
                'supplier_expenses': expense_metrics['supplier_expenses']
            },
            'category_performance': category_metrics,
            'transactions_count': sales_metrics['total_sales'],
            'average_transaction_value': sales_metrics['avg_sale'] or 0,
            'daily_trend': list(daily_sales),
            'customer_metrics': {
                'total_customers': customer_metrics['total_customers'] or 0,
                'avg_customer_value': customer_metrics['avg_customer_value'] or 0
            },
            'supplier_specific': supplier_specific
        }

    def generate_monthly_report_for_supplier(self, month, year, supplier=None):
        """Generate monthly report for a specific supplier"""
        start_date = datetime(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day)

        # Get metrics for the specific month
        metrics = self.calculate_financial_metrics_for_supplier(supplier, start_date, end_date)

        # Get additional monthly insights
        monthly_transactions = Transaction.objects.filter(
            date__year=year,
            date__month=month
        )

        # Add supplier filter if needed
        if supplier:
            monthly_transactions = monthly_transactions.filter(
                Q(produit__supplier=supplier) |
                Q(from_user=supplier) |
                Q(to_user=supplier)
            )
        
        # Calculate real customer insights
        customer_metrics = monthly_transactions.filter(
            customer__isnull=False
        ).aggregate(
            total_customers=Count('customer', distinct=True),
            avg_purchase_value=Avg(F('price') * F('quantity'), output_field=DecimalField())
        )

        # Calculate daily performance
        daily_performance = monthly_transactions.annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            revenue=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type='sale'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            expenses=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type__in=['purchase', 'supplier_purchase']), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            profit=F('revenue') - F('expenses'),
            transactions=Count('id')
        ).order_by('day')

        # Calculate best and worst days
        best_day = None
        worst_day = None
        if daily_performance:
            best_day = max(daily_performance, key=lambda x: x['revenue'])
            worst_day = min(daily_performance, key=lambda x: x['revenue'])

        return {
            'month': month,
            'year': year,
            'revenue': metrics['summary']['total_revenue'],
            'expenses': metrics['summary']['total_expenses'],
            'profit': metrics['summary']['gross_profit'],
            'profit_margin': metrics['summary']['profit_margin'],
            'category_performance': metrics['category_performance'],
            'inventory_value': metrics['inventory']['total_value'],
            'inventory_items': metrics['inventory']['total_items'],
            'transaction_metrics': {
                'total_count': metrics['transactions_count'],
                'average_value': metrics['average_transaction_value']
            },
            'customer_insights': {
                'total_customers': customer_metrics['total_customers'] or 0,
                'avg_purchase_value': customer_metrics['avg_purchase_value'] or 0
            },
            'daily_performance': list(daily_performance),
            'best_day': best_day,
            'worst_day': worst_day,
            'supplier_specific': metrics.get('supplier_specific', {})
        }

    def get_yearly_comparison_for_supplier(self, year, supplier=None):
        """Generate year-over-year comparison for a specific supplier"""
        current_year_metrics = self.calculate_financial_metrics_for_supplier(
            supplier=supplier,
            start_date=datetime(year, 1, 1),
            end_date=datetime(year, 12, 31)
        )
        
        previous_year_metrics = self.calculate_financial_metrics_for_supplier(
            supplier=supplier,
            start_date=datetime(year-1, 1, 1),
            end_date=datetime(year-1, 12, 31)
        )
        
        # Calculate monthly trends for current year
        monthly_trends = []
        for month in range(1, 13):
            start_date = datetime(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day)
            
            monthly_data = self.calculate_financial_metrics_for_supplier(
                supplier=supplier,
                start_date=start_date,
                end_date=end_date
            )
            
            monthly_trends.append({
                'month': month,
                'revenue': monthly_data['summary']['total_revenue'],
                'expenses': monthly_data['summary']['total_expenses'],
                'profit': monthly_data['summary']['gross_profit'],
                'units_sold': monthly_data['summary']['units_sold']
            })
        
        # Calculate growth metrics
        revenue_growth = 0
        profit_growth = 0
        
        if previous_year_metrics['summary']['total_revenue'] > 0:
            revenue_growth = ((current_year_metrics['summary']['total_revenue'] / 
                             previous_year_metrics['summary']['total_revenue']) * 100) - 100
                             
        if previous_year_metrics['summary']['gross_profit'] > 0:
            profit_growth = ((current_year_metrics['summary']['gross_profit'] / 
                            previous_year_metrics['summary']['gross_profit']) * 100) - 100
        
        return {
            'current_year': current_year_metrics,
            'previous_year': previous_year_metrics,
            'growth': {
                'revenue': revenue_growth,
                'profit': profit_growth,
                'inventory_value': ((current_year_metrics['inventory']['total_value'] / 
                                   previous_year_metrics['inventory']['total_value']) * 100) - 100
                                   if previous_year_metrics['inventory']['total_value'] > 0 else 0,
                'transactions': ((current_year_metrics['transactions_count'] / 
                                previous_year_metrics['transactions_count']) * 100) - 100
                                if previous_year_metrics['transactions_count'] > 0 else 0
            },
            'monthly_trends': monthly_trends
        }

    def get_top_selling_products(self, n=5, supplier=None):
        """Get real top-selling products using database aggregation"""
        products = Produit.objects
        
        if supplier:
            products = products.filter(supplier=supplier)
            
        return products.annotate(
            total_sales=Coalesce(Sum('transaction__quantity', filter=Q(transaction__type='sale')), 0),
            revenue=Coalesce(Sum(F('transaction__quantity') * F('transaction__price'), 
                       filter=Q(transaction__type='sale'), output_field=DecimalField()), Value(0, output_field=DecimalField()))
        ).filter(total_sales__gt=0).order_by('-total_sales')[:n]

    def get_most_profitable_products(self, n=5, supplier=None):
        """Get most profitable products"""
        products = Produit.objects
        
        if supplier:
            products = products.filter(supplier=supplier)
            
        return products.annotate(
            revenue=Coalesce(Sum(F('transaction__quantity') * F('transaction__price'), 
                       filter=Q(transaction__type='sale'), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            cost=Coalesce(Sum(F('transaction__quantity') * F('transaction__price'), 
                     filter=Q(transaction__type__in=['purchase', 'supplier_purchase']), output_field=DecimalField()), Value(0, output_field=DecimalField())),
            profit=F('revenue') - F('cost')
        ).filter(revenue__gt=0).order_by('-profit')[:n]

    def get_inventory_health(self, supplier=None):
        """Calculate inventory health metrics"""
        products = Produit.objects
        
        if supplier:
            products = products.filter(supplier=supplier)
        
        # Calculate low stock items
        low_stock = products.filter(quantity__lte=10).count()
        
        # Calculate out of stock items
        out_of_stock = products.filter(quantity=0).count()
        
        # Calculate inventory turnover
        # (Cost of Goods Sold / Average Inventory Value)
        now = datetime.now()
        start_of_year = datetime(now.year, 1, 1)
        
        cogs = Transaction.objects.filter(
            type='sale',
            date__gte=start_of_year
        )
        
        if supplier:
            cogs = cogs.filter(
                Q(produit__supplier=supplier) |
                Q(from_user=supplier)
            )
            
        cogs_value = cogs.aggregate(
            total=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        inventory_value = products.aggregate(
            value=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['value']
        
        inventory_turnover = cogs_value / inventory_value if inventory_value > 0 else 0
        
        return {
            'total_products': products.count(),
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'inventory_value': inventory_value,
            'inventory_turnover': inventory_turnover,
            'days_on_hand': 365 / inventory_turnover if inventory_turnover > 0 else 0
        }

    def get_customer_insights(self, supplier=None):
        """Get customer insights"""
        transactions = Transaction.objects.filter(
            type='sale',
            customer__isnull=False
        )
        
        if supplier:
            transactions = transactions.filter(
                Q(produit__supplier=supplier) |
                Q(from_user=supplier)
            )
        
        # Top customers by revenue
        top_customers = transactions.values('customer__name').annotate(
            total_spent=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            purchases=Count('id'),
            last_purchase=Max('date')
        ).order_by('-total_spent')[:10]
        
        # Customer retention
        repeat_customers = transactions.values('customer').annotate(
            purchase_count=Count('id')
        ).filter(purchase_count__gt=1).count()
        
        total_customers = transactions.values('customer').distinct().count()
        
        retention_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
        
        return {
            'top_customers': list(top_customers),
            'total_customers': total_customers,
            'repeat_customers': repeat_customers,
            'retention_rate': retention_rate,
            'average_purchase': transactions.aggregate(
                avg=Avg(F('price') * F('quantity'), output_field=DecimalField())
            )['avg'] or 0
        }