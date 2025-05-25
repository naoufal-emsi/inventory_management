# Inventory Management System

## 1. Project Overview

This Inventory Management System is a full-stack web application designed to help businesses efficiently track and manage their stock, suppliers, and sales. The system supports role-based access (admin, staff, supplier), product and transaction management, customer purchase tracking, and more. It is built with Django (Python) for the backend and uses PostgreSQL for data storage. The frontend is rendered with Django templates and styled with modern CSS.

### Core Features
- **Product Tracking:** Add, edit, delete, and view products in inventory.
- **Stock Adjustment:** Record sales and purchases, automatically updating stock levels.
- **Low-Stock Alerts:** Highlight products with low stock (configurable threshold).
- **Supplier Management:** Manage suppliers and link products to suppliers.
- **Role-Based Access:** Admin (superuser), staff, and supplier roles with different permissions.
- **Customer Management:** Staff/admin can add customer details and record their purchases.
- **Activity Logging:** Track user actions for auditing.
- **Dashboard & Analytics:** View key stats and recent activity.

## 2. Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL (or SQLite for dev/testing)
- Node.js & npm (if you want to add a JS frontend)
- Git

### Clone the Repository
```sh
git clone <REPO_URL>
cd inventorymanagment/inventory_web
```

### Create and Activate Virtual Environment
```sh
python3 -m venv env
source env/bin/activate
```

### Install Python Dependencies
```sh
pip install -r requirements.txt
```

### Database Setup
- **PostgreSQL:**
  1. Create a database named `inventory`:
     ```sh
     psql -U postgres -c 'CREATE DATABASE inventory;'
     ```
  2. Update `inventory_web/settings.py` with your DB credentials if needed.
- **SQLite:** No setup needed (default for Django if not changed).

### Environment Variables
Create a `.env` file in `inventory_web/` (if using secrets):
```
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://postgres:0000@localhost:5432/inventory
```

### Run Migrations
```sh
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser (Admin)
```sh
python manage.py createsuperuser
```

### Start the Development Server
```sh
python manage.py runserver
```

### Setup Quirks & Bugs
- If you change the user model, you must drop and recreate the database.
- If migrations fail due to model changes, try `python manage.py migrate --fake-initial` or drop/recreate DB.
- Only admin can access Django admin panel; staff/supplier use the web UI.

## 3. Codebase Structure

```
SrockMaster/
  models.py         # All Django models (Product, User, Supplier, etc.)
  views.py          # Django views (controllers)
  admin.py          # Django admin registration
  urls.py           # App URL routes
  services/
    inventory_manager.py  # Business logic for inventory
    manager.py            # Reporting/analytics logic
  templates/        # HTML templates (Django)
  static/
    css/style.css   # Main CSS
    js/main.js      # JS for UI
  migrations/       # Django migrations
```

- **models.py:** All database models (Product, User, Supplier, Customer, Purchase, etc.)
- **views.py:** All business logic and request handling
- **services/:** Helper classes for inventory and reporting
- **templates/:** All HTML pages (Django templates)
- **static/:** CSS and JS assets

## 4. Detailed Class Breakdown

### class CustomUser(AbstractUser)
- **Properties:**
  - username, email, password, ... (from Django)
  - user_type: str ('admin', 'staff', 'supplier')
- **Purpose:** Main user model for authentication and role management.

### class Produit(models.Model)
- **Properties:**
  - name: str
  - price: float
  - quantity: int
  - category: str
  - supplier: FK to CustomUser (supplier)
- **Methods:**
  - __str__(): Display name
- **Purpose:** Represents a product in inventory.

### class SupplierProfile(models.Model)
- **Properties:**
  - user: OneToOne(CustomUser)
  - company_name, contact, email, phone, address
- **Purpose:** Extra info for supplier users.

### class StaffProfile(models.Model)
- **Properties:**
  - user: OneToOne(CustomUser)
  - phone
- **Purpose:** Extra info for staff users.

### class Customer(models.Model)
- **Properties:**
  - name, email, phone, address
- **Purpose:** Represents a customer (added by staff/admin).

### class Purchase(models.Model)
- **Properties:**
  - customer: FK to Customer
  - product: FK to Produit
  - quantity: int
  - price: float
  - date: datetime
  - added_by: FK to CustomUser
- **Purpose:** Records a purchase made by a customer.

### class Transaction(models.Model)
- **Properties:**
  - produit: FK to Produit
  - type: str ('sale', 'purchase')
  - quantity: int
  - price: float
  - date: date
- **Purpose:** Records sales and purchases for inventory.

### class ActivityLog(models.Model)
- **Properties:**
  - user: FK to CustomUser
  - action: str
  - timestamp: datetime
  - details: str
- **Purpose:** Logs user actions for auditing.

## 5. Current Project Status

| Feature                        | Status        |
|------------------------------- |--------------|
| User login/signup              | [x] Complete |
| Product model                  | [x] Complete |
| Inventory API/views            | [x] Complete |
| Supplier CRUD                  | [x] Complete |
| Customer & Purchase tracking   | [x] Complete |
| Role-based access              | [x] Complete |
| Low-stock alerts               | [x] Complete |
| Activity log                   | [x] Complete |
| Analytics dashboard            | [x] Complete |
| User roles & dashboards           | [ ] Supplier/staff dashboards, sessions not finished |
| Unit tests                       | [ ] Not started |
| Profile/settings page             | [ ] Needs improvement |

## 6. Next Steps / TODOs for Teammate

- [ ] Finalize Supplier CRUD UI and permissions
- [ ] Integrate low-stock email/UI alerts
- [ ] Add unit tests for inventory, user, and purchase logic
- [ ] Improve frontend product search/filter (see `main.js`)
- [ ] Add REST API endpoints for inventory and transactions
- [ ] Refactor and document all forms
- [ ] Add pagination to product and customer lists
- [ ] Improve error handling and user feedback
- [ ] Review and clean up all TODO comments in code

## 7. Developer Notes

- If you change the user model, you must drop and recreate the database and rerun all migrations.
- Some legacy code for customers may still exist; only staff/admin should add customers.
- Supplier users can only manage their own products; staff/admin can manage all.
- The UI is built with Django templates and custom CSS (see `static/css/style.css`).
- TODOs are marked in code, especially in views and forms.
- For questions, contact the previous developer or check the commit history for context.

---

**Contact:**
- If you need more context, check the code comments or reach out via the project Slack/email.
