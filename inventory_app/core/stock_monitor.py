import json
import os

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "../data/products.json")

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

def get_low_stock_products(threshold):
    products = load_products()
    return [
        {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": product["quantity"],
            "category": product["category"]
        }
        for product in products if product['quantity'] <= threshold
    ]

def auto_restock(min_level, restock_to):
    products = load_products()
    changed = False
    for product in products:
        if product['quantity'] < min_level:
            product['quantity'] = restock_to
            changed = True
    if changed:
        save_products(products)

def calculate_stock_value():
    products = load_products()
    return sum(product['price'] * product['quantity'] for product in products)

def get_inventory_by_category():
    products = load_products()
    inventory_by_category = {}
    for product in products:
        category = product['category']
        info = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": product["quantity"],
            "category": product["category"]
        }
        if category not in inventory_by_category:
            inventory_by_category[category] = []
        inventory_by_category[category].append(info)
    return inventory_by_category