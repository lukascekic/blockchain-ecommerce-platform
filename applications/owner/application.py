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

    sold_items = database.session.query(
        Product.name,
        database.func.sum(OrderItem.quantity).label('total')
    ).join(OrderItem).join(Order).filter(Order.status == 'COMPLETE').group_by(Product.name).all()

    waiting_items = database.session.query(
        Product.name,
        database.func.sum(OrderItem.quantity).label('total')
    ).join(OrderItem).join(Order).filter(Order.status.in_(['CREATED', 'PENDING'])).group_by(Product.name).all()

    sold_dict = {item.name: int(item.total) for item in sold_items}
    waiting_dict = {item.name: int(item.total) for item in waiting_items}

    all_names = set(sold_dict.keys()) | set(waiting_dict.keys())

    statistics = []
    for name in all_names:
        statistics.append({
            "name": name,
            "sold": sold_dict.get(name, 0),
            "waiting": waiting_dict.get(name, 0)
        })

    return jsonify({"statistics": statistics}), 200


@application.route('/category_statistics', methods=['GET'])
@jwt_required()
def category_statistics():
    jwt_data = get_jwt()
    if 'owner' not in jwt_data.get('roles', []):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    all_categories = Category.query.all()

    sold_by_category = database.session.query(
        Category.name,
        database.func.sum(OrderItem.quantity).label('total')
    ).join(ProductCategory, Category.id == ProductCategory.category_id)\
     .join(Product, ProductCategory.product_id == Product.id)\
     .join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status == 'COMPLETE')\
     .group_by(Category.name).all()

    sold_dict = {cat.name: int(cat.total) for cat in sold_by_category}

    category_list = []
    for category in all_categories:
        total_sold = sold_dict.get(category.name, 0)
        category_list.append((category.name, total_sold))

    category_list.sort(key=lambda x: (-x[1], x[0]))

    statistics = [cat[0] for cat in category_list]

    return jsonify({"statistics": statistics}), 200


if __name__ == '__main__':
    with application.app_context():
        database.create_all()

    application.run(host='0.0.0.0', port=5000, debug=True)
