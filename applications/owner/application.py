import sys
import os

# Add parent directory to path to import shared models and configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, case
from configuration import application, database
from models import Product, Category, ProductCategory, Order, OrderItem
import io
import csv

def role_check(required_role):
    """Decorator to check if user has required role"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            roles = claims.get('roles', [])
            if required_role not in roles:
                return jsonify({"msg": "Missing Authorization Header"}), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


@application.route('/update', methods=['POST'])
@jwt_required()
@role_check('owner')
def update():
    """
    Owner uploads CSV file with products and categories.
    CSV format: category1|category2|...,product_name,price
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({"message": "Field file is missing."}), 400

    file = request.files['file']

    # Read file content
    try:
        content = file.stream.read().decode('utf-8')
    except Exception:
        return jsonify({"message": "Field file is missing."}), 400

    # Parse CSV
    csv_reader = csv.reader(io.StringIO(content))

    products_to_add = []

    for line_number, row in enumerate(csv_reader, start=0):
        # Each row must have exactly 3 values
        if len(row) != 3:
            return jsonify({"message": f"Incorrect number of values on line {line_number}."}), 400

        categories_str, product_name, price_str = row

        # Validate price
        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError
        except ValueError:
            return jsonify({"message": f"Incorrect price on line {line_number}."}), 400

        # Parse categories (pipe-separated)
        category_names = [cat.strip() for cat in categories_str.split('|') if cat.strip()]

        products_to_add.append({
            'name': product_name.strip(),
            'price': price,
            'categories': category_names,
            'line_number': line_number
        })

    # Check for duplicate product names BEFORE adding anything to database
    for product_data in products_to_add:
        existing_product = Product.query.filter_by(name=product_data['name']).first()
        if existing_product:
            return jsonify({"message": f"Product {product_data['name']} already exists."}), 400

    # All validations passed - now add products to database
    try:
        for product_data in products_to_add:
            # Create new product
            product = Product(
                name=product_data['name'],
                price=product_data['price']
            )
            database.session.add(product)
            database.session.flush()  # Get product.id without committing

            # Process categories
            for category_name in product_data['categories']:
                # Find or create category
                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    category = Category(name=category_name)
                    database.session.add(category)
                    database.session.flush()  # Get category.id

                # Create ProductCategory link
                product_category = ProductCategory(
                    product_id=product.id,
                    category_id=category.id
                )
                database.session.add(product_category)

        database.session.commit()
        return '', 200

    except Exception as e:
        database.session.rollback()
        return jsonify({"message": str(e)}), 400


@application.route('/product_statistics', methods=['GET'])
@jwt_required()
@role_check('owner')
def product_statistics():
    """
    Returns statistics for each product: how many sold and how many waiting.
    Only includes products that have been sold at least once.
    """
    # Query:
    # - Join Product -> OrderItem -> Order
    # - SUM quantity grouped by product
    # - CASE for sold (status='COMPLETE') and waiting (status IN ('CREATED', 'PENDING'))
    # - Filter: sold > 0

    stats = database.session.query(
        Product.name,
        func.sum(
            case(
                (Order.status == 'COMPLETE', OrderItem.quantity),
                else_=0
            )
        ).label('sold'),
        func.sum(
            case(
                (Order.status.in_(['CREATED', 'PENDING']), OrderItem.quantity),
                else_=0
            )
        ).label('waiting')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).group_by(
        Product.id, Product.name
    ).all()

    statistics = [
        {
            "name": name,
            "sold": int(sold),
            "waiting": int(waiting)
        }
        for name, sold, waiting in stats
    ]

    return jsonify({"statistics": statistics}), 200


@application.route('/category_statistics', methods=['GET'])
@jwt_required()
@role_check('owner')
def category_statistics():
    """
    Returns list of categories ordered by number of sold products.
    Includes ALL categories that have products, sorted by COMPLETE order count.
    Order: by count DESC (COMPLETE orders only), then by name ASC.
    """
    # Query:
    # - LEFT JOIN to include categories even if no COMPLETE orders
    # - Calculate sold count from COMPLETE orders only
    # - ORDER BY sold count DESC, name ASC

    # Subquery to count sold items from COMPLETE orders per category
    sold_subquery = database.session.query(
        Category.id.label('category_id'),
        func.sum(
            case(
                (Order.status == 'COMPLETE', OrderItem.quantity),
                else_=0
            )
        ).label('sold_count')
    ).join(
        ProductCategory, Category.id == ProductCategory.category_id
    ).join(
        Product, ProductCategory.product_id == Product.id
    ).outerjoin(
        OrderItem, Product.id == OrderItem.product_id
    ).outerjoin(
        Order, OrderItem.order_id == Order.id
    ).group_by(
        Category.id
    ).subquery()

    # Main query: sve kategorije sa sold_count
    stats = database.session.query(
        Category.name,
        func.coalesce(sold_subquery.c.sold_count, 0).label('count')
    ).outerjoin(
        sold_subquery, Category.id == sold_subquery.c.category_id
    ).order_by(
        func.coalesce(sold_subquery.c.sold_count, 0).desc(),
        Category.name.asc()
    ).all()

    statistics = [name for name, count in stats]

    return jsonify({"statistics": statistics}), 200


if __name__ == '__main__':
    # Initialize database tables
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
