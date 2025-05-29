from SrockMaster.models import Transaction, Produit
from collections import Counter
from django.db.models import Sum, F, Q, Count, Avg
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from calendar import monthrange

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
            revenue=Sum(F('price') * F('quantity')),
            total_sales=Count('id'),
            avg_sale=Avg(F('price') * F('quantity'))
        )

        # Calculate expenses using database aggregation
        expense_metrics = transactions.filter(
            Q(type='purchase') | Q(type='supplier_purchase')
        ).aggregate(
            total_expenses=Sum(F('price') * F('quantity')),
            purchase_expenses=Sum(F('price') * F('quantity'), filter=Q(type='purchase')),
            supplier_expenses=Sum(F('price') * F('quantity'), filter=Q(type='supplier_purchase'))
        )

        # Calculate category performance using database queries
        category_metrics = {}
        categories = Produit.objects.values_list('category', flat=True).distinct()
        
        for category in categories:
            cat_transactions = transactions.filter(produit__category=category)
            
            sales = cat_transactions.filter(type='sale').aggregate(
                revenue=Sum(F('price') * F('quantity')),
                units=Sum('quantity')
            )
            
            expenses = cat_transactions.filter(
                Q(type='purchase') | Q(type='supplier_purchase')
            ).aggregate(
                expenses=Sum(F('price') * F('quantity'))
            )
            
            category_metrics[category] = {
                'revenue': sales['revenue'] or 0,
                'expenses': expenses['expenses'] or 0,
                'profit': (sales['revenue'] or 0) - (expenses['expenses'] or 0),
                'units_sold': sales['units'] or 0
            }

        # Calculate actual totals
        total_revenue = sales_metrics['revenue'] or 0
        total_expenses = expense_metrics['total_expenses'] or 0
        gross_profit = total_revenue - total_expenses

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'gross_profit': gross_profit,
                'profit_margin': (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
            },
            'expense_breakdown': {
                'purchase_expenses': expense_metrics['purchase_expenses'] or 0,
                'supplier_expenses': expense_metrics['supplier_expenses'] or 0
            },
            'category_performance': category_metrics,
            'transactions_count': sales_metrics['total_sales'] or 0,
            'average_transaction_value': sales_metrics['avg_sale'] or 0
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
        
        # Calculate revenue using database aggregation
        sales_metrics = transactions.filter(type='sale').aggregate(
            revenue=Sum(F('price') * F('quantity')),
            total_sales=Count('id'),
            avg_sale=Avg(F('price') * F('quantity'))
        )

        # Calculate expenses using database aggregation
        expense_metrics = transactions.filter(
            Q(type='purchase') | Q(type='supplier_purchase')
        ).aggregate(
            total_expenses=Sum(F('price') * F('quantity')),
            purchase_expenses=Sum(F('price') * F('quantity'), filter=Q(type='purchase')),
            supplier_expenses=Sum(F('price') * F('quantity'), filter=Q(type='supplier_purchase'))
        )

        # Calculate category performance using database queries
        category_metrics = {}
        categories = Produit.objects.values_list('category', flat=True).distinct()
        
        for category in categories:
            cat_transactions = transactions.filter(produit__category=category)
            
            sales = cat_transactions.filter(type='sale').aggregate(
                revenue=Sum(F('price') * F('quantity')),
                units=Sum('quantity')
            )
            
            expenses = cat_transactions.filter(
                Q(type='purchase') | Q(type='supplier_purchase')
            ).aggregate(
                expenses=Sum(F('price') * F('quantity'))
            )
            
            category_metrics[category] = {
                'revenue': sales['revenue'] or 0,
                'expenses': expenses['expenses'] or 0,
                'profit': (sales['revenue'] or 0) - (expenses['expenses'] or 0),
                'units_sold': sales['units'] or 0
            }

        # Calculate actual totals
        total_revenue = sales_metrics['revenue'] or 0
        total_expenses = expense_metrics['total_expenses'] or 0
        gross_profit = total_revenue - total_expenses

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'gross_profit': gross_profit,
                'profit_margin': (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
            },
            'expense_breakdown': {
                'purchase_expenses': expense_metrics['purchase_expenses'] or 0,
                'supplier_expenses': expense_metrics['supplier_expenses'] or 0
            },
            'category_performance': category_metrics,
            'transactions_count': sales_metrics['total_sales'] or 0,
            'average_transaction_value': sales_metrics['avg_sale'] or 0
        }

    def get_top_selling_products(self, n=5):
        """Get real top-selling products using database aggregation"""
        return Produit.objects.annotate(
            total_sales=Sum('transaction__quantity', filter=Q(transaction__type='sale')),
            revenue=Sum(F('transaction__quantity') * F('transaction__price'), 
                       filter=Q(transaction__type='sale'))
        ).filter(total_sales__gt=0).order_by('-total_sales')[:n]

    def generate_monthly_report(self, month, year):
        """Generate detailed monthly report using real transaction data"""
        start_date = datetime(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day)

        # Get metrics for the specific month
        metrics = self.calculate_financial_metrics(start_date, end_date)

        # Get additional monthly insights
        monthly_transactions = Transaction.objects.filter(
            date__year=year,
            date__month=month
        )

        # Calculate real customer insights
        customer_metrics = monthly_transactions.filter(
            customer__isnull=False
        ).aggregate(
            total_customers=Count('customer', distinct=True),
            avg_purchase_value=Avg(F('price') * F('quantity'))
        )

        return {
            'month': month,
            'year': year,
            'revenue': metrics['summary']['total_revenue'],
            'expenses': metrics['summary']['total_expenses'],
            'profit': metrics['summary']['gross_profit'],
            'profit_margin': metrics['summary']['profit_margin'],
            'category_performance': metrics['category_performance'],
            'transaction_metrics': {
                'total_count': metrics['transactions_count'],
                'average_value': metrics['average_transaction_value']
            },
            'customer_insights': {
                'total_customers': customer_metrics['total_customers'] or 0,
                'avg_purchase_value': customer_metrics['avg_purchase_value'] or 0
            }
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
            avg_purchase_value=Avg(F('price') * F('quantity'))
        )

        return {
            'month': month,
            'year': year,
            'revenue': metrics['summary']['total_revenue'],
            'expenses': metrics['summary']['total_expenses'],
            'profit': metrics['summary']['gross_profit'],
            'profit_margin': metrics['summary']['profit_margin'],
            'category_performance': metrics['category_performance'],
            'transaction_metrics': {
                'total_count': metrics['transactions_count'],
                'average_value': metrics['average_transaction_value']
            },
            'customer_insights': {
                'total_customers': customer_metrics['total_customers'] or 0,
                'avg_purchase_value': customer_metrics['avg_purchase_value'] or 0
            }
        }

    def get_yearly_comparison(self, year):
        """Generate year-over-year comparison"""
        current_year_metrics = self.calculate_financial_metrics(
            start_date=datetime(year, 1, 1),
            end_date=datetime(year, 12, 31)
        )
        
        previous_year_metrics = self.calculate_financial_metrics(
            start_date=datetime(year-1, 1, 1),
            end_date=datetime(year-1, 12, 31)
        )
        
        return {
            'current_year': current_year_metrics,
            'previous_year': previous_year_metrics,
            'growth': {
                'revenue': ((current_year_metrics['summary']['total_revenue'] / 
                           previous_year_metrics['summary']['total_revenue'] * 100) - 100)
                           if previous_year_metrics['summary']['total_revenue'] > 0 else 0,
                'profit': ((current_year_metrics['summary']['gross_profit'] / 
                          previous_year_metrics['summary']['gross_profit'] * 100) - 100)
                          if previous_year_metrics['summary']['gross_profit'] > 0 else 0
            }
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
        
        return {
            'current_year': current_year_metrics,
            'previous_year': previous_year_metrics,
            'growth': {
                'revenue': ((current_year_metrics['summary']['total_revenue'] / 
                           previous_year_metrics['summary']['total_revenue'] * 100) - 100)
                           if previous_year_metrics['summary']['total_revenue'] > 0 else 0,
                'profit': ((current_year_metrics['summary']['gross_profit'] / 
                          previous_year_metrics['summary']['gross_profit'] * 100) - 100)
                          if previous_year_metrics['summary']['gross_profit'] > 0 else 0
            }
        }

    def get_top_selling_products(self, n=5):
        """Get real top-selling products using database aggregation"""
        return Produit.objects.annotate(
            total_sales=Sum('transaction__quantity', filter=Q(transaction__type='sale')),
            revenue=Sum(F('transaction__quantity') * F('transaction__price'), 
                       filter=Q(transaction__type='sale'))
        ).filter(total_sales__gt=0).order_by('-total_sales')[:n]

    def get_most_expensive_product(self):
        return Produit.objects.order_by('-price').first()

    def average_product_price(self):
        products = Produit.objects.all()
        if not products.exists():
            return 0
        total = sum(p.price for p in products)
        return total / products.count()
