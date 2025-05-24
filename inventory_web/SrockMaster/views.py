# SrockMaster/views.py
from django.shortcuts import render, redirect
from SrockMaster.services.inventory_manager import InventoryManager

inventory = InventoryManager()

def inventaire_view(request):
    if request.method == 'POST':
        data = {
            "name": request.POST.get("name"),
            "price": float(request.POST.get("price")),
            "quantity": int(request.POST.get("quantity")),
            "category": request.POST.get("category"),
        }
        inventory.add_product(data)
        return redirect('inventaire')

    produits = inventory.list_all_products()
    return render(request, 'inventaire.html', {"produits": produits})
