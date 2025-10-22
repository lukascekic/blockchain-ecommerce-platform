import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

blockchain_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'blockchain'))
sys.path.insert(0, blockchain_path)

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from configuration import application, database
from models import Product, Category, ProductCategory, Order, OrderItem
from web3 import Web3
import json

GANACHE_URL = os.environ.get('GANACHE_URL', 'http://ganache:8545')
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

OWNER_PRIVATE_KEY = os.environ.get('OWNER_PRIVATE_KEY', None)

from deploy import deploy_payment_contract
from utils import check_is_paid, build_pay_transaction, confirm_delivery_tx

@application.route('/search', methods=['GET'])
@jwt_required()
def search():
    jwt_data = get_jwt()
    if 'customer' not in jwt_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    product_name = request.args.get('name', '')
    category_name = request.args.get('category', '')

    products_query = database.session.query(Product).distinct()

    if product_name:
        products_query = products_query.filter(Product.name.like('%{}%'.format(product_name)))

    if category_name:
        products_query = products_query.join(Product.categories).filter(
            Category.name.like('%{}%'.format(category_name))
        )

    products = products_query.all()

    categories_query = database.session.query(Category).distinct()

    if category_name:
        categories_query = categories_query.filter(Category.name.like('%{}%'.format(category_name)))

    if product_name:
        categories_query = categories_query.join(Category.products).filter(
            Product.name.like('%{}%'.format(product_name))
        )

    categories = categories_query.all()

    categories_list = []
    for category in categories:
        categories_list.append(category.name)

    products_list = []
    for product in products:
        categories_query = database.session.query(Category.name).join(
            ProductCategory
        ).filter(ProductCategory.product_id == product.id).all()

        product_categories = [cat.name for cat in categories_query]

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
def order():
    user_data = get_jwt()
    if 'customer' not in user_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    customer_email = user_data['sub']

    req_body = request.get_json()

    if 'requests' not in req_body:
        return jsonify({"message": "Field requests is missing."}), 400

    requests_list = req_body['requests']

    for index, req in enumerate(requests_list):
        if 'id' not in req:
            return jsonify({"message": "Product id is missing for request number {}.".format(index)}), 400

        if 'quantity' not in req:
            return jsonify({"message": "Product quantity is missing for request number {}.".format(index)}), 400

        try:
            product_id = int(req['id'])
            if product_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid product id for request number {}.".format(index)}), 400

        try:
            quantity = int(req['quantity'])
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid product quantity for request number {}.".format(index)}), 400

    for index, req in enumerate(requests_list):
        product_id = int(req['id'])
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify({"message": "Invalid product for request number {}.".format(index)}), 400

    if 'address' not in req_body or not req_body['address']:
        return jsonify({"message": "Field address is missing."}), 400

    customer_address = req_body['address']

    if not web3.is_address(customer_address):
        return jsonify({"message": "Invalid address."}), 400

    try:
        total_price = 0.0
        order_items_data = []

        for req in requests_list:
            product_id = int(req['id'])
            quantity = int(req['quantity'])

            product = Product.query.filter_by(id=product_id).first()

            item_total = product.price * quantity
            total_price += item_total

            order_items_data.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': product.price
            })

        new_order = Order(
            customer_email=customer_email,
            price=total_price,
            status='CREATED',
            timestamp=datetime.utcnow()
        )

        if customer_address and OWNER_PRIVATE_KEY:
            amount_wei = int(total_price * 100)

            contract_address = deploy_payment_contract(
                web3,
                OWNER_PRIVATE_KEY,
                customer_address,
                amount_wei
            )

            new_order.contract_address = contract_address
            new_order.customer_address = customer_address

        database.session.add(new_order)
        database.session.flush()

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

    except Exception as error:
        database.session.rollback()
        return jsonify({"message": str(error)}), 400


@application.route('/pay', methods=['POST'])
@application.route('/generate_invoice', methods=['POST'])
@jwt_required()
def pay():
    user_roles = get_jwt().get('roles', [])
    if 'customer' not in user_roles:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    customer_email = get_jwt()['sub']

    json_data = request.get_json()

    if 'id' not in json_data:
        return jsonify({"message": "Missing order id."}), 400

    try:
        order_id = int(json_data['id'])
        if order_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid order id."}), 400

    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({"message": "Invalid order id."}), 400

    if order.customer_email != customer_email:
        return jsonify({"message": "Invalid order id."}), 400

    if 'address' not in json_data:
        return jsonify({"message": "Missing address."}), 400

    customer_address = json_data['address']

    if not customer_address or not web3.is_address(customer_address):
        return jsonify({"message": "Invalid address."}), 400

    if not order.contract_address:
        return jsonify({"message": "Invalid order id."}), 400

    if check_is_paid(web3, order.contract_address):
        return jsonify({"message": "Transfer already complete."}), 400

    amount_wei = int(order.price * 100)
    transaction = build_pay_transaction(
        web3,
        order.contract_address,
        customer_address,
        amount_wei
    )

    return jsonify({"invoice": transaction}), 200


@application.route('/status', methods=['GET'])
@jwt_required()
def status():
    jwt_data = get_jwt()
    if 'customer' not in jwt_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    customer_email = jwt_data['sub']

    orders = Order.query.filter_by(customer_email=customer_email).all()

    orders_list = []
    for order in orders:
        items_query = database.session.query(
            OrderItem.quantity,
            OrderItem.price,
            Product.id.label('product_id'),
            Product.name.label('product_name')
        ).join(Product).filter(OrderItem.order_id == order.id).all()

        products = []
        for item in items_query:
            categories_query = database.session.query(Category.name).join(
                ProductCategory
            ).filter(ProductCategory.product_id == item.product_id).all()

            product_categories = [cat.name for cat in categories_query]

            products.append({
                "categories": product_categories,
                "name": item.product_name,
                "price": item.price,
                "quantity": item.quantity
            })

        order_dict = {
            "products": products,
            "price": order.price,
            "status": order.status,
            "timestamp": order.timestamp.isoformat() + 'Z'
        }

        orders_list.append(order_dict)

    return jsonify({"orders": orders_list}), 200


@application.route('/delivered', methods=['POST'])
@jwt_required()
def delivered():
    user_data = get_jwt()
    if 'customer' not in user_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    customer_email = user_data['sub']

    req_data = request.get_json()

    if 'id' not in req_data:
        return jsonify({"message": "Missing order id."}), 400

    try:
        order_id = int(req_data['id'])
        if order_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid order id."}), 400

    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({"message": "Invalid order id."}), 400

    if order.customer_email != customer_email:
        return jsonify({"message": "Invalid order id."}), 400

    if order.status == 'CREATED':
        return jsonify({"message": "Delivery not complete."}), 400

    if order.status != 'PENDING':
        return jsonify({"message": "Invalid order id."}), 400

    order.status = 'COMPLETE'

    if order.contract_address and OWNER_PRIVATE_KEY:
        try:
            confirm_delivery_tx(web3, order.contract_address, OWNER_PRIVATE_KEY)
        except Exception as error:
            database.session.rollback()
            return jsonify({"message": str(error)}), 400

    database.session.commit()

    return '', 200


if __name__ == '__main__':
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
