from SrockMaster.models import Produit

class InventoryManager:
    def list_all_products(self):
        return Produit.objects.all()

    def add_product(self, data):
        return Produit.objects.create(**data)

    def update_product(self, produit_id, updates):
        produit = Produit.objects.get(id=produit_id)
        for key, value in updates.items():
            setattr(produit, key, value)
        produit.save()
        return produit

    def delete_product(self, produit_id):
        Produit.objects.get(id=produit_id).delete()

    def search_by_name(self, name):
        return Produit.objects.filter(name__icontains=name)

    def sort_by_field(self, field):
        return Produit.objects.all().order_by(field)
