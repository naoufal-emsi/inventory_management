import json
import os
from collections import Counter

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "../data/products.json")
TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "../data/transactions.json")

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def load_transactions():
    with open(TRANSACTIONS_FILE, "r") as f:
        return json.load(f)

def generate_monthly_report(month, year):
    transactions = load_transactions()
    filtered_transactions = [t for t in transactions if t['date'].startswith(f"{year}-{month:02d}")]
    revenue = sum(t['price'] * t['quantity'] for t in filtered_transactions if t['type'] == 'sale')
    expenses = sum(t['price'] * t['quantity'] for t in filtered_transactions if t['type'] == 'purchase')
    profit = revenue - expenses
    return {'revenue': revenue, 'expenses': expenses, 'profit': profit}

def get_top_selling_products(n):
    transactions = load_transactions()
    products = load_products()
    sales_count = Counter(t['product_id'] for t in transactions if t['type'] == 'sale')
    top_selling_ids = [item[0] for item in sales_count.most_common(n)]
    return [product for product in products if product['id'] in top_selling_ids]

def get_most_expensive_product():
    products = load_products()
    return max(products, key=lambda x: x['price'])

def average_product_price():
    products = load_products()
    return sum(product['price'] for product in products) / len(products) if products else 0