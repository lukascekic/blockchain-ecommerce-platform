import sys
import os

# Add parent directory to path to import shared models and configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import and_, or_
from datetime import datetime
from configuration import application, database
from models import Product, Category, ProductCategory, Order, OrderItem

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


@application.route('/search', methods=['GET'])
@jwt_required()
@role_check('customer')
def search():
    """
    Search for products and categories.
    Query parameters: name (optional), category (optional)
    """
    product_name = request.args.get('name', '')
    category_name = request.args.get('category', '')

    # Query products
    products_query = database.session.query(Product).distinct()

    # Filter by product name (LIKE)
    if product_name:
        products_query = products_query.filter(Product.name.like(f'%{product_name}%'))

    # Filter by category name (JOIN + LIKE)
    if category_name:
        products_query = products_query.join(
            Product.categories
        ).filter(
            Category.name.like(f'%{category_name}%')
        )

    products = products_query.all()

    # Query categories
    categories_query = database.session.query(Category).distinct()

    # Filter by category name (LIKE)
    if category_name:
        categories_query = categories_query.filter(Category.name.like(f'%{category_name}%'))

    # Filter by product name (JOIN + LIKE)
    if product_name:
        categories_query = categories_query.join(
            Category.products
        ).filter(
            Product.name.like(f'%{product_name}%')
        )

    categories = categories_query.all()

    # Format response
    categories_list = [category.name for category in categories]

    products_list = []
    for product in products:
        product_categories = [cat.name for cat in product.categories]
        products_list.append({
            "categories": product_categories,
            "id": product.id,
            "name": product.name,
            "price": product.price
        })

    return jsonify({
        "categories": categories_list,
        "products": products_list
    }), 200


@application.route('/order', methods=['POST'])
@jwt_required()
@role_check('customer')
def order():
    """
    Create a new order.
    Request body: {"requests": [{"id": 1, "quantity": 2}, ...]}
    """
    claims = get_jwt()
    customer_email = claims['sub']

    data = request.get_json()

    # Validation: requests field missing
    if 'requests' not in data:
        return jsonify({"message": "Field requests is missing."}), 400

    requests_list = data['requests']

    # Validate each request
    for index, req in enumerate(requests_list):
        # Check if 'id' is missing
        if 'id' not in req:
            return jsonify({"message": f"Product id is missing for request number {index}."}), 400

        # Check if 'quantity' is missing
        if 'quantity' not in req:
            return jsonify({"message": f"Product quantity is missing for request number {index}."}), 400

        # Validate id is positive integer
        try:
            product_id = int(req['id'])
            if product_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": f"Invalid product id for request number {index}."}), 400

        # Validate quantity is positive integer
        try:
            quantity = int(req['quantity'])
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": f"Invalid product quantity for request number {index}."}), 400

        # Check if product exists
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify({"message": f"Invalid product for request number {index}."}), 400

    # All validations passed - create order
    try:
        # Calculate total price
        total_price = 0.0
        order_items_data = []

        for req in requests_list:
            product_id = int(req['id'])
            quantity = int(req['quantity'])

            product = Product.query.filter_by(id=product_id).first()

            # Snapshot price at time of order
            item_total = product.price * quantity
            total_price += item_total

            order_items_data.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': product.price  # Snapshot price
            })

        # Create order
        new_order = Order(
            customer_email=customer_email,
            price=total_price,
            status='CREATED',
            timestamp=datetime.utcnow()
        )
        database.session.add(new_order)
        database.session.flush()  # Get order.id

        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            database.session.add(order_item)

        database.session.commit()

        return jsonify({"id": new_order.id}), 200

    except Exception as e:
        database.session.rollback()
        return jsonify({"message": str(e)}), 400


@application.route('/status', methods=['GET'])
@jwt_required()
@role_check('customer')
def status():
    """
    Get all orders for the current customer.
    """
    claims = get_jwt()
    customer_email = claims['sub']

    # Query all orders for this customer
    orders = Order.query.filter_by(customer_email=customer_email).all()

    orders_list = []
    for order in orders:
        # Get order items with products
        products = []
        for item in order.items:
            product = item.product
            product_categories = [cat.name for cat in product.categories]

            products.append({
                "categories": product_categories,
                "name": product.name,
                "price": item.price,  # Snapshot price from OrderItem
                "quantity": item.quantity
            })

        order_dict = {
            "products": products,
            "price": order.price,
            "status": order.status,
            "timestamp": order.timestamp.isoformat() + 'Z'  # ISO 8601 format
        }

        orders_list.append(order_dict)

    return jsonify({"orders": orders_list}), 200


@application.route('/delivered', methods=['POST'])
@jwt_required()
@role_check('customer')
def delivered():
    """
    Mark an order as delivered (COMPLETE).
    Request body: {"id": 123}
    """
    claims = get_jwt()
    customer_email = claims['sub']

    data = request.get_json()

    # Validation: id missing
    if 'id' not in data:
        return jsonify({"message": "Missing order id."}), 400

    # Validate id is positive integer
    try:
        order_id = int(data['id'])
        if order_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid order id."}), 400

    # Find order
    order = Order.query.filter_by(id=order_id).first()

    # Check if order exists
    if not order:
        return jsonify({"message": "Invalid order id."}), 400

    # Check if order belongs to this customer
    if order.customer_email != customer_email:
        return jsonify({"message": "Invalid order id."}), 400

    # Check if order is in PENDING status
    if order.status == 'CREATED':
        return jsonify({"message": "Delivery not complete."}), 400

    if order.status != 'PENDING':
        return jsonify({"message": "Invalid order id."}), 400

    # Update status to COMPLETE
    order.status = 'COMPLETE'
    database.session.commit()

    return '', 200


if __name__ == '__main__':
    # Initialize database tables
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
