import sys
import os

# Add parent directory to path to import shared models and configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from configuration import application, database
from models import Order, CourierAssignment

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


@application.route('/orders_to_deliver', methods=['GET'])
@jwt_required()
@role_check('courier')
def orders_to_deliver():
    """
    Get all orders that are ready for pickup (status = CREATED).
    Returns: {"orders": [{"id": ..., "email": ...}, ...]}
    """
    # Query all orders with status CREATED
    orders = Order.query.filter_by(status='CREATED').all()

    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "email": order.customer_email
        })

    return jsonify({"orders": orders_list}), 200


@application.route('/pick_up_order', methods=['POST'])
@jwt_required()
@role_check('courier')
def pick_up_order():
    """
    Mark an order as picked up by the courier (CREATED -> PENDING).
    Request body: {"id": 123}
    """
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

    # Check if order status is CREATED
    if order.status != 'CREATED':
        return jsonify({"message": "Invalid order id."}), 400

    # Update status to PENDING
    order.status = 'PENDING'
    database.session.commit()

    return '', 200


if __name__ == '__main__':
    # Initialize database tables
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
