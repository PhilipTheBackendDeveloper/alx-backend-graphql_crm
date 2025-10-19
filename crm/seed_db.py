"""
Database seeding script for CRM system
Run with: python manage.py shell < seed_db.py
Or create as a management command
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order
from django.db import transaction
from decimal import Decimal


def clear_database():
    """Clear all existing data"""
    print("Clearing existing data...")
    Order.objects.all().delete()
    Customer.objects.all().delete()
    Product.objects.all().delete()
    print("Database cleared!")


def seed_customers():
    """Seed customer data"""
    print("\nSeeding customers...")
    customers = [
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol Williams", "email": "carol@example.com", "phone": "+9876543210"},
        {"name": "David Brown", "email": "david@example.com", "phone": "555-123-4567"},
        {"name": "Eve Davis", "email": "eve@example.com", "phone": "+1122334455"},
        {"name": "Frank Miller", "email": "frank@example.com"},
        {"name": "Grace Lee", "email": "grace@example.com", "phone": "999-888-7777"},
        {"name": "Henry Wilson", "email": "henry@example.com"},
        {"name": "Ivy Martinez", "email": "ivy@example.com", "phone": "+5544332211"},
        {"name": "Jack Taylor", "email": "jack@example.com", "phone": "111-222-3333"},
    ]
    
    created_customers = []
    for customer_data in customers:
        customer = Customer.objects.create(**customer_data)
        created_customers.append(customer)
        print(f"  Created: {customer.name} ({customer.email})")
    
    print(f"✓ Created {len(created_customers)} customers")
    return created_customers


def seed_products():
    """Seed product data"""
    print("\nSeeding products...")
    products = [
        {"name": "Laptop", "price": Decimal("999.99"), "stock": 50},
        {"name": "Mouse", "price": Decimal("29.99"), "stock": 200},
        {"name": "Keyboard", "price": Decimal("79.99"), "stock": 150},
        {"name": "Monitor", "price": Decimal("299.99"), "stock": 75},
        {"name": "Headphones", "price": Decimal("149.99"), "stock": 100},
        {"name": "Webcam", "price": Decimal("89.99"), "stock": 60},
        {"name": "USB Cable", "price": Decimal("9.99"), "stock": 500},
        {"name": "External SSD", "price": Decimal("199.99"), "stock": 80},
        {"name": "Desk Lamp", "price": Decimal("39.99"), "stock": 120},
        {"name": "Office Chair", "price": Decimal("249.99"), "stock": 40},
        {"name": "Notebook", "price": Decimal("12.99"), "stock": 300},
        {"name": "Pen Set", "price": Decimal("19.99"), "stock": 250},
    ]
    
    created_products = []
    for product_data in products:
        product = Product.objects.create(**product_data)
        created_products.append(product)
        print(f"  Created: {product.name} - ${product.price} (Stock: {product.stock})")
    
    print(f"✓ Created {len(created_products)} products")
    return created_products


def seed_orders(customers, products):
    """Seed order data with product associations"""
    print("\nSeeding orders...")
    
    orders_data = [
        {"customer_idx": 0, "product_indices": [0, 1, 2]},  # Alice: Laptop, Mouse, Keyboard
        {"customer_idx": 1, "product_indices": [3, 4]},     # Bob: Monitor, Headphones
        {"customer_idx": 2, "product_indices": [5]},        # Carol: Webcam
        {"customer_idx": 3, "product_indices": [0, 3, 4]},  # David: Laptop, Monitor, Headphones
        {"customer_idx": 4, "product_indices": [6, 7]},     # Eve: USB Cable, External SSD
        {"customer_idx": 5, "product_indices": [8, 9]},     # Frank: Desk Lamp, Office Chair
        {"customer_idx": 6, "product_indices": [10, 11]},   # Grace: Notebook, Pen Set
        {"customer_idx": 7, "product_indices": [1, 2, 6]},  # Henry: Mouse, Keyboard, USB Cable
        {"customer_idx": 8, "product_indices": [4, 5]},     # Ivy: Headphones, Webcam
        {"customer_idx": 9, "product_indices": [0, 1, 2, 3, 4]},  # Jack: Multiple items
    ]
    
    created_orders = []
    for order_data in orders_data:
        customer = customers[order_data["customer_idx"]]
        order_products = [products[idx] for idx in order_data["product_indices"]]
        
        with transaction.atomic():
            order = Order.objects.create(customer=customer)
            order.products.set(order_products)
            
            # Calculate total amount
            total = sum(p.price for p in order_products)
            order.total_amount = total
            order.save()
            
            created_orders.append(order)
            product_names = ", ".join([p.name for p in order_products])
            print(f"  Created: Order #{order.id} for {customer.name} - ${order.total_amount} ({product_names})")
    
    print(f"✓ Created {len(created_orders)} orders")
    return created_orders


def main():
    """Main seeding function"""
    print("=" * 60)
    print("CRM Database Seeding Script")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Clear existing data
            clear_database()
            
            # Seed data
            customers = seed_customers()
            products = seed_products()
            orders = seed_orders(customers, products)
            
            print("\n" + "=" * 60)
            print("Database seeding completed successfully!")
            print("=" * 60)
            print(f"\nSummary:")
            print(f"  Customers: {len(customers)}")
            print(f"  Products:  {len(products)}")
            print(f"  Orders:    {len(orders)}")
            print("\nYou can now test the GraphQL API at /graphql")
            
    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        raise


if __name__ == "__main__":
    main()