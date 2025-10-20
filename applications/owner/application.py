import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from configuration import application, database
from models import Product, Category, ProductCategory, Order, OrderItem
import io
import csv

@application.route('/update', methods=['POST'])
@jwt_required()
def update():
    jwt_data = get_jwt()
    if 'owner' not in jwt_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    if 'file' not in request.files:
        return jsonify({"message": "Field file is missing."}), 400

    file = request.files['file']

    try:
        content = file.stream.read().decode('utf-8')
    except Exception:
        return jsonify({"message": "Field file is missing."}), 400

    csv_reader = csv.reader(io.StringIO(content))

    products_to_add = []

    line_num = 0
    for row in csv_reader:
        if len(row) != 3:
            return jsonify({"message": "Incorrect number of values on line %d." % line_num}), 400

        categories_str, product_name, price_str = row

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError
        except ValueError:
            return jsonify({"message": "Incorrect price on line %d." % line_num}), 400

        category_names = [cat.strip() for cat in categories_str.split('|') if cat.strip()]

        products_to_add.append({
            'name': product_name.strip(),
            'price': price,
            'categories': category_names,
            'line_number': line_num
        })

        line_num += 1

    for product_data in products_to_add:
        existing_product = Product.query.filter_by(name=product_data['name']).first()
        if existing_product:
            return jsonify({"message": "Product {} already exists.".format(product_data['name'])}), 400

    try:
        for product_data in products_to_add:
            product = Product(
                name=product_data['name'],
                price=product_data['price']
            )
            database.session.add(product)
            database.session.flush()

            for category_name in product_data['categories']:
                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    category = Category(name=category_name)
                    database.session.add(category)
                    database.session.flush()

                product_category = ProductCategory(
                    product_id=product.id,
                    category_id=category.id
                )
                database.session.add(product_category)

        database.session.commit()
        return '', 200

    except Exception as error:
        database.session.rollback()
        return jsonify({"message": str(error)}), 400


@application.route('/product_statistics', methods=['GET'])
@jwt_required()
def product_statistics():
    user_roles = get_jwt().get('roles', [])
    if 'owner' not in user_roles:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    all_products = Product.query.join(OrderItem).join(Order).all()

    product_stats = {}
    for product in all_products:
        if product.name not in product_stats:
            product_stats[product.name] = {'sold': 0, 'waiting': 0}

        for item in product.order_items:
            if item.order.status == 'COMPLETE':
                product_stats[product.name]['sold'] += item.quantity
            elif item.order.status in ['CREATED', 'PENDING']:
                product_stats[product.name]['waiting'] += item.quantity

    statistics = []
    for name, stats in product_stats.items():
        statistics.append({
            "name": name,
            "sold": int(stats['sold']),
            "waiting": int(stats['waiting'])
        })

    return jsonify({"statistics": statistics}), 200


@application.route('/category_statistics', methods=['GET'])
@jwt_required()
def category_statistics():
    jwt_data = get_jwt()
    if 'owner' not in jwt_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    all_categories = Category.query.all()

    category_counts = []
    for category in all_categories:
        sold_count = 0

        for product in category.products:
            for order_item in product.order_items:
                if order_item.order.status == 'COMPLETE':
                    sold_count += order_item.quantity

        category_counts.append({
            'name': category.name,
            'count': sold_count
        })

    category_counts.sort(key=lambda x: (-x['count'], x['name']))

    statistics = []
    for item in category_counts:
        statistics.append(item['name'])

    return jsonify({"statistics": statistics}), 200


if __name__ == '__main__':
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
