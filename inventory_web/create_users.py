import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_web.settings')
django.setup()

from SrockMaster.models import CustomUser
from django.utils import timezone

# Define user data
users_data = []

# 20 suppliers
for i in range(1, 21):
    users_data.append({
        'username': f'supplier{i}',
        'first_name': f'FirstNameSup{i}',
        'last_name': f'LastNameSup{i}',
        'user_type': 'supplier',
        'contact': f'supplier{i}@example.com',
        'phone': f'07000000{i:02}',
        'address': f'{i} Supplier Street, City {chr(64 + i)}'
    })

# 10 staff
for i in range(1, 11):
    users_data.append({
        'username': f'staff{i}',
        'first_name': f'FirstNameStaff{i}',
        'last_name': f'LastNameStaff{i}',
        'user_type': 'staff',
        'contact': f'staff{i}@example.com',
        'phone': f'07100000{i:02}',
        'address': f'{i} Staff Avenue, City {chr(64 + i)}'
    })

# Create users
for data in users_data:
    user = CustomUser(
        username=data['username'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        user_type=data['user_type'],
        contact=data['contact'],
        phone=data['phone'],
        address=data['address'],
        date_joined=timezone.now(),
        balance=0.00
    )
    user.set_password('inventory12')
    user.save()
    print(f"Created user: {data['username']}")

print("✅ All users created successfully!")
