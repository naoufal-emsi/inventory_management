# main.py

from core.inventory_ops import *
from core.stock_monitor import *
from core.transaction_ops import *
from core.reports import *
from datetime import datetime

def menu_inventaire():
    while True:
        print("\n--- Opérations d'inventaire ---")
        print("1. Ajouter un produit")
        print("2. Modifier un produit")
        print("3. Supprimer un produit")
        print("4. Rechercher un produit par nom")
        print("5. Trier les produits par champ")
        print("6. Lister tous les produits")
        print("7. Retour au menu principal")
        choix = input("Sélectionnez une option : ")

        if choix == "1":
            pid = int(input("ID : "))
            nom = input("Nom : ")
            prix = float(input("Prix : "))
            quantite = int(input("Quantité : "))
            categorie = input("Catégorie : ")
            add_product({"id": pid, "name": nom, "price": prix, "quantity": quantite, "category": categorie})
            print("Produit ajouté avec succès.")
        elif choix == "2":
            pid = int(input("ID du produit à modifier : "))
            champ = input("Champ à modifier (name/price/quantity/category) : ")
            valeur = input("Nouvelle valeur : ")
            if champ in ["price", "quantity"]:
                valeur = float(valeur) if champ == "price" else int(valeur)
            update_product(pid, {champ: valeur})
            print("Produit modifié avec succès.")
        elif choix == "3":
            delete_product(int(input("ID du produit à supprimer : ")))
            print("Produit supprimé avec succès.")
        elif choix == "4":
            print(search_product_by_name(input("Nom à rechercher : ")))
        elif choix == "5":
            print(sort_products_by(input("Trier par champ (name/price/quantity/category) : ")))
        elif choix == "6":
            print(list_all_products())
        elif choix == "7":
            break

def menu_stock():
    while True:
        print("\n--- Suivi du stock ---")
        print("1. Voir les produits en faible stock")
        print("2. Réapprovisionnement automatique")
        print("3. Calculer la valeur du stock")
        print("4. Inventaire par catégorie")
        print("5. Retour au menu principal")
        choix = input("Sélectionnez une option : ")

        if choix == "1":
            print(get_low_stock_products(int(input("Seuil : "))))
        elif choix == "2":
            auto_restock(int(input("Niveau minimum : ")), int(input("Réapprovisionner à : ")))
            print("Réapprovisionnement effectué.")
        elif choix == "3":
            print("Valeur totale du stock :", calculate_stock_value())
        elif choix == "4":
            print(get_inventory_by_category())
        elif choix == "5":
            break

def menu_transactions():
    while True:
        print("\n--- Transactions ---")
        print("1. Vendre un produit")
        print("2. Acheter un produit")
        print("3. Voir l'historique des transactions")
        print("4. Retour au menu principal")
        choix = input("Sélectionnez une option : ")

        if choix == "1":
            sell_product(int(input("ID du produit : ")), int(input("Quantité : ")))
            print("Vente enregistrée.")
        elif choix == "2":
            purchase_product(int(input("ID du produit : ")), int(input("Quantité : ")), float(input("Coût par unité : ")))
            print("Achat enregistré.")
        elif choix == "3":
            print(view_transaction_history())
        elif choix == "4":
            break

def menu_rapports():
    while True:
        print("\n--- Rapports ---")
        print("1. Générer un rapport mensuel")
        print("2. Produits les plus vendus")
        print("3. Produit le plus cher")
        print("4. Prix moyen des produits")
        print("5. Retour au menu principal")
        choix = input("Sélectionnez une option : ")

        if choix == "1":
            mois = int(input("Mois (1-12) : "))
            annee = int(input("Année (ex : 2025) : "))
            print(generate_monthly_report(mois, annee))
        elif choix == "2":
            print(get_top_selling_products(int(input("Nombre de produits à afficher : "))))
        elif choix == "3":
            print(get_most_expensive_product())
        elif choix == "4":
            print("Prix moyen :", average_product_price())
        elif choix == "5":
            break

def main():
    while True:
        print("\n=== Système de gestion d'inventaire ===")
        print("1. Opérations d'inventaire")
        print("2. Suivi du stock")
        print("3. Transactions")
        print("4. Rapports")
        print("5. Quitter")
        option = input("Choisissez une option : ")

        if option == "1":
            menu_inventaire()
        elif option == "2":
            menu_stock()
        elif option == "3":
            menu_transactions()
        elif option == "4":
            menu_rapports()
        elif option == "5":
            print("Fermeture du programme...")
            break
        else:
            print("Option invalide !")

if __name__ == "__main__":
    main()