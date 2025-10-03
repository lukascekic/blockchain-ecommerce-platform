"""
Test script za proveru Store modela i relationships.
Ovo je INTERNI test fajl - ne predaje se u projektu!
"""

from configuration import application, database
from models import Product, Category, ProductCategory, Order, OrderItem, CourierAssignment
from datetime import datetime

def test_database_creation():
    """Test kreiranje tabela"""
    print("=" * 50)
    print("TEST 1: Kreiranje tabela")
    print("=" * 50)

    with application.app_context():
        # Brisanje svih tabela (fresh start)
        database.drop_all()
        print("✅ Sve tabele obrisane")

        # Kreiranje svih tabela
        database.create_all()
        print("✅ Sve tabele kreirane")

        # Provera da li tabele postoje
        inspector = database.inspect(database.engine)
        tables = inspector.get_table_names()
        print(f"\n📋 Kreirane tabele: {tables}")

        expected_tables = ['categories', 'products', 'product_categories', 'orders', 'order_items', 'courier_assignments']
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING!")

def test_product_category_relationship():
    """Test Product-Category many-to-many relationship"""
    print("\n" + "=" * 50)
    print("TEST 2: Product-Category Relationship")
    print("=" * 50)

    with application.app_context():
        # Kreiranje kategorija
        cat1 = Category(name='Electronics')
        cat2 = Category(name='Computers')
        database.session.add_all([cat1, cat2])
        database.session.commit()
        print(f"✅ Kategorije kreirane: {cat1}, {cat2}")

        # Kreiranje proizvoda
        product = Product(name='Laptop', price=999.99)
        product.categories.append(cat1)
        product.categories.append(cat2)
        database.session.add(product)
        database.session.commit()
        print(f"✅ Proizvod kreiran: {product}")

        # Provera relationships
        print(f"\n📋 Proizvod '{product.name}' pripada kategorijama:")
        for cat in product.categories:
            print(f"  - {cat.name}")

        print(f"\n📋 Kategorija '{cat1.name}' sadrži proizvode:")
        for prod in cat1.products:
            print(f"  - {prod.name} (${prod.price})")

def test_order_creation():
    """Test Order, OrderItem i relationships"""
    print("\n" + "=" * 50)
    print("TEST 3: Order Creation & Items")
    print("=" * 50)

    with application.app_context():
        # Dohvatanje proizvoda
        laptop = Product.query.filter_by(name='Laptop').first()

        # Kreiranje još proizvoda
        mouse = Product(name='Mouse', price=29.99)
        keyboard = Product(name='Keyboard', price=79.99)
        database.session.add_all([mouse, keyboard])
        database.session.commit()

        # Kreiranje narudžbine
        order = Order(
            customer_email='test@test.com',
            price=1109.97,  # 999.99 + 29.99 + 79.99
            status='CREATED',
            timestamp=datetime.utcnow()
        )
        database.session.add(order)
        database.session.flush()  # Da dobijemo order.id

        # Kreiranje order items
        item1 = OrderItem(order_id=order.id, product_id=laptop.id, quantity=1, price=laptop.price)
        item2 = OrderItem(order_id=order.id, product_id=mouse.id, quantity=2, price=mouse.price)
        item3 = OrderItem(order_id=order.id, product_id=keyboard.id, quantity=1, price=keyboard.price)

        database.session.add_all([item1, item2, item3])
        database.session.commit()

        print(f"✅ Narudžbina kreirana: {order}")
        print(f"\n📋 Stavke narudžbine:")
        for item in order.items:
            print(f"  - {item.product.name} x{item.quantity} = ${item.price * item.quantity}")
        print(f"  💰 UKUPNO: ${order.price}")

def test_courier_assignment():
    """Test CourierAssignment"""
    print("\n" + "=" * 50)
    print("TEST 4: Courier Assignment")
    print("=" * 50)

    with application.app_context():
        # Dohvatanje narudžbine
        order = Order.query.first()

        # Kreiranje courier assignment
        courier = CourierAssignment(
            order_id=order.id,
            courier_address='0x1234567890abcdef'
        )
        database.session.add(courier)
        database.session.commit()

        print(f"✅ Kurir dodeljen narudžbini: {courier}")
        print(f"\n📋 Narudžbina {order.id}:")
        print(f"  - Status: {order.status}")
        print(f"  - Kurir: {order.courier_info.courier_address if order.courier_info else 'Nije dodeljen'}")

def test_cascade_delete():
    """Test cascade delete - brisanje Order briše i OrderItem i CourierAssignment"""
    print("\n" + "=" * 50)
    print("TEST 5: Cascade Delete")
    print("=" * 50)

    with application.app_context():
        # Brojanje stavki PRE brisanja
        items_before = OrderItem.query.count()
        couriers_before = CourierAssignment.query.count()
        print(f"PRE brisanja: {items_before} order items, {couriers_before} courier assignments")

        # Brisanje narudžbine
        order = Order.query.first()
        database.session.delete(order)
        database.session.commit()
        print(f"✅ Narudžbina {order.id} obrisana")

        # Brojanje stavki POSLE brisanja
        items_after = OrderItem.query.count()
        couriers_after = CourierAssignment.query.count()
        print(f"POSLE brisanja: {items_after} order items, {couriers_after} courier assignments")

        if items_after == 0 and couriers_after == 0:
            print("✅ CASCADE DELETE radi! Stavke automatski obrisane.")
        else:
            print("❌ CASCADE DELETE NE RADI!")

if __name__ == '__main__':
    print("\n🧪 TESTIRANJE STORE MODELA\n")

    test_database_creation()
    test_product_category_relationship()
    test_order_creation()
    test_courier_assignment()
    test_cascade_delete()

    print("\n" + "=" * 50)
    print("✅ SVI TESTOVI ZAVRŠENI!")
    print("=" * 50)
