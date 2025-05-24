from SrockMaster.models import Transaction, Produit
from collections import Counter

class Manager:
    def generate_monthly_report(self, month, year):
        transactions = Transaction.objects.filter(date__year=year, date__month=month)
        revenue = sum(t.price * t.quantity for t in transactions if t.type == 'sale')
        expenses = sum(t.price * t.quantity for t in transactions if t.type == 'purchase')
        profit = revenue - expenses
        return {
            'mois': month,
            'année': year,
            'revenu': revenue,
            'dépenses': expenses,
            'profit': profit
        }

    def get_top_selling_products(self, n=5):
        transactions = Transaction.objects.filter(type='sale')
        counter = Counter([t.produit.id for t in transactions])
        top_ids = [item[0] for item in counter.most_common(n)]
        return Produit.objects.filter(id__in=top_ids)

    def get_most_expensive_product(self):
        return Produit.objects.order_by('-price').first()

    def average_product_price(self):
        products = Produit.objects.all()
        if not products.exists():
            return 0
        total = sum(p.price for p in products)
        return total / products.count()
