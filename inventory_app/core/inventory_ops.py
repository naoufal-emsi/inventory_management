import json
import os

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "../data/products.json")

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

def add_product(product):
    products = load_products()
    products.append(product)
    save_products(products)

def update_product(product_id, new_data):
    products = load_products()
    for product in products:
        if product['id'] == product_id:
            product.update(new_data)
            break
    save_products(products)

def delete_product(product_id):
    products = load_products()
    products = [product for product in products if product['id'] != product_id]
    save_products(products)

def search_product_by_name(name):
    products = load_products()
    return [product for product in products if name.lower() in product['name'].lower()]

def sort_products_by(field):
    products = load_products()
    return sorted(products, key=lambda x: x.get(field))

def list_all_products():
    return load_products()