import os
from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

application = Flask(__name__)

application.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/authentication')
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

application.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'JWT_SECRET_DEV_KEY')
application.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=3600)
application.config['JWT_TOKEN_LOCATION'] = ['headers']

database = SQLAlchemy(application)
jwt = JWTManager(application)
