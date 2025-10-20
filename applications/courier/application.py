import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

blockchain_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'blockchain'))
sys.path.insert(0, blockchain_path)

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from configuration import application, database
from models import Order, CourierAssignment
from web3 import Web3

GANACHE_URL = os.environ.get('GANACHE_URL', 'http://ganache:8545')
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

OWNER_PRIVATE_KEY = os.environ.get('OWNER_PRIVATE_KEY', None)

from utils import check_is_paid, assign_courier_tx


@application.route('/orders_to_deliver', methods=['GET'])
@jwt_required()
def orders_to_deliver():
    jwt_data = get_jwt()
    if 'courier' not in jwt_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

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
def pick_up_order():
    user_roles = get_jwt().get('roles', [])
    if 'courier' not in user_roles:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    req_data = request.get_json()

    if 'id' not in req_data:
        return jsonify({"message": "Missing order id."}), 400

    try:
        order_id = int(req_data['id'])
        if order_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid order id."}), 400

    courier_address = req_data.get('address', None)
    if courier_address:
        if not web3.is_address(courier_address):
            return jsonify({"message": "Invalid address."}), 400

    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({"message": "Invalid order id."}), 400

    if order.status != 'CREATED':
        return jsonify({"message": "Invalid order id."}), 400

    if order.contract_address and courier_address:
        if not check_is_paid(web3, order.contract_address):
            return jsonify({"message": "Transfer not complete."}), 400

        if OWNER_PRIVATE_KEY:
            try:
                assign_courier_tx(web3, order.contract_address, courier_address, OWNER_PRIVATE_KEY)

                courier_assignment = CourierAssignment(
                    order_id=order.id,
                    courier_address=courier_address
                )
                database.session.add(courier_assignment)
            except Exception as error:
                return jsonify({"message": str(error)}), 400

    order.status = 'PENDING'
    database.session.commit()

    return '', 200


if __name__ == '__main__':
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
