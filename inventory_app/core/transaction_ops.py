import json
import os
from datetime import datetime

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "../data/products.json")
TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "../data/transactions.json")

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

def load_transactions():
    with open(TRANSACTIONS_FILE, "r") as f:
        return json.load(f)

def save_transactions(transactions):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=4)

def sell_product(product_id, quantity):
    products = load_products()
    transactions = load_transactions()
    for product in products:
        if product['id'] == product_id and product['quantity'] >= quantity:
            product['quantity'] -= quantity
            transactions.append({
                "type": "sale",
                "product_id": product_id,
                "product_name": product['name'],
                "quantity": quantity,
                "price": product['price'],
                "date": datetime.today().strftime('%Y-%m-%d')
            })
            save_products(products)
            save_transactions(transactions)
            break

def purchase_product(product_id, quantity, cost):
    products = load_products()
    transactions = load_transactions()
    for product in products:
        if product['id'] == product_id:
            product['quantity'] += quantity
            transactions.append({
                "type": "purchase",
                "product_id": product_id,
                "product_name": product['name'],
                "quantity": quantity,
                "price": cost,
                "date": datetime.today().strftime('%Y-%m-%d')
            })
            save_products(products)
            save_transactions(transactions)
            break

def view_transaction_history():
    return load_transactions()