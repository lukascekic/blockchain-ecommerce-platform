from configuration import database

class ProductCategory(database.Model):
    __tablename__ = 'product_categories'

    product_id = database.Column(database.Integer, database.ForeignKey('products.id'), primary_key=True)
    category_id = database.Column(database.Integer, database.ForeignKey('categories.id'), primary_key=True)

    def __repr__(self):
        return '<ProductCategory product_id=%d category_id=%d>' % (self.product_id, self.category_id)


class Product(database.Model):
    __tablename__ = 'products'

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    price = database.Column(database.Float, nullable=False)

    categories = database.relationship(
        'Category',
        secondary='product_categories',
        back_populates='products'
    )
    order_items = database.relationship('OrderItem', back_populates='product')

    def __repr__(self):
        return '<Product {} (${})>'.format(self.name, self.price)


class Category(database.Model):
    __tablename__ = 'categories'

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship(
        'Product',
        secondary='product_categories',
        back_populates='categories'
    )

    def __repr__(self):
        return '<Category {}>'.format(self.name)


class Order(database.Model):
    __tablename__ = 'orders'

    id = database.Column(database.Integer, primary_key=True)
    customer_email = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)
    status = database.Column(database.String(64), nullable=False, default='CREATED')
    timestamp = database.Column(database.DateTime, nullable=False)

    contract_address = database.Column(database.String(256), nullable=True)
    customer_address = database.Column(database.String(256), nullable=True)

    items = database.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    courier_info = database.relationship('CourierAssignment', back_populates='order', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return '<Order %d - %s ($%s) [%s]>' % (self.id, self.customer_email, self.price, self.status)


class OrderItem(database.Model):
    __tablename__ = 'order_items'

    id = database.Column(database.Integer, primary_key=True)
    order_id = database.Column(database.Integer, database.ForeignKey('orders.id'), nullable=False)
    product_id = database.Column(database.Integer, database.ForeignKey('products.id'), nullable=False)
    quantity = database.Column(database.Integer, nullable=False)
    price = database.Column(database.Float, nullable=False)

    order = database.relationship('Order', back_populates='items')
    product = database.relationship('Product', back_populates='order_items')

    def __repr__(self):
        return '<OrderItem order={} product={} qty={}>'.format(self.order_id, self.product_id, self.quantity)


class CourierAssignment(database.Model):
    __tablename__ = 'courier_assignments'

    id = database.Column(database.Integer, primary_key=True)
    order_id = database.Column(database.Integer, database.ForeignKey('orders.id'), unique=True, nullable=False)
    courier_address = database.Column(database.String(256), nullable=False)

    order = database.relationship('Order', back_populates='courier_info')

    def __repr__(self):
        return '<CourierAssignment order={} courier={}>'.format(self.order_id, self.courier_address)
