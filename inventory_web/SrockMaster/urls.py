from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inventory/', views.inventory, name='inventory'),
    path('transactions/', views.transactions, name='transactions'),
    path('reports/', views.reports, name='reports'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('transaction/sale/', views.record_sale, name='record_sale'),
    path('transaction/purchase/', views.record_purchase, name='record_purchase'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('suppliers/', views.suppliers, name='suppliers'),
    path('customers/', views.customers, name='customers'),
    path('activity-log/', views.activity_log, name='activity_log'),
    path('analytics/', views.analytics, name='analytics'),
    path('analytics/users/<str:user_type>/', views.user_details, name='user_details'),
    path('support/', views.support, name='support'),
]

urlpatterns += [
    path('supplier/<int:supplier_id>/products/', views.supplier_products, name='supplier_products'),
]