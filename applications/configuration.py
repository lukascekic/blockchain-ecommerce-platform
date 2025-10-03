import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Kreiranje Flask aplikacije (shared za sve store servise)
application = Flask(__name__)

# Database konfiguracija
application.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/store')
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT konfiguracija (ista kao u authentication servisu)
application.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'JWT_SECRET_DEV_KEY')
application.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=3600)  # Tačno 1 sat
application.config['JWT_TOKEN_LOCATION'] = ['headers']

# Inicijalizacija ekstenzija
database = SQLAlchemy(application)
jwt = JWTManager(application)
