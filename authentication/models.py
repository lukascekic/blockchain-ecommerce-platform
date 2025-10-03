from configuration import database

class User(database.Model):
    __tablename__ = 'users'

    id = database.Column(database.Integer, primary_key=True)
    forename = database.Column(database.String(256), nullable=False)
    surname = database.Column(database.String(256), nullable=False)
    email = database.Column(database.String(256), nullable=False, unique=True)
    password = database.Column(database.String(256), nullable=False)
    role = database.Column(database.String(64), nullable=False)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
