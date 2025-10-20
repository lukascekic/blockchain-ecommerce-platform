import re
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from passlib.hash import sha256_crypt
from email_validator import validate_email, EmailNotValidError
from configuration import application, database
from models import User
from sqlalchemy import and_

# Email regex pattern prema specifikaciji
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_registration_data(data, role):
    """
    Validira podatke za registraciju prema TAČNOM redosledu iz specifikacije.
    Vraća (error_message, status_code) ili (None, None) ako je sve ok.
    """
    # 1. Provera forename
    if 'forename' not in data or not data['forename']:
        return {"message": "Field forename is missing."}, 400

    # 2. Provera surname
    if 'surname' not in data or not data['surname']:
        return {"message": "Field surname is missing."}, 400

    # 3. Provera email
    if 'email' not in data or not data['email']:
        return {"message": "Field email is missing."}, 400

    # 4. Provera password (MORA PRE email format validacije!)
    if 'password' not in data or not data['password']:
        return {"message": "Field password is missing."}, 400

    # 5. Email format validacija
    if not re.match(EMAIL_REGEX, data['email']):
        return {"message": "Invalid email."}, 400

    # 6. Password length validacija
    if len(data['password']) < 8:
        return {"message": "Invalid password."}, 400

    # 7. Email uniqueness
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return {"message": "Email already exists."}, 400

    return None, None

@application.route('/register_customer', methods=['POST'])
def register_customer():
    """
    Registracija kupca.
    Endpoint: POST /register_customer
    """
    data = request.get_json()

    # Validacija
    error, status = validate_registration_data(data, 'customer')
    if error:
        return jsonify(error), status

    # Kreiranje korisnika
    hashed_password = sha256_crypt.hash(data['password'])
    user = User(
        forename=data['forename'],
        surname=data['surname'],
        email=data['email'],
        password=hashed_password,
        role='customer'
    )

    database.session.add(user)
    database.session.commit()

    return '', 200

@application.route('/register_courier', methods=['POST'])
def register_courier():
    """
    Registracija kurira.
    Endpoint: POST /register_courier
    """
    data = request.get_json()

    # Validacija (ista kao za customer)
    error, status = validate_registration_data(data, 'courier')
    if error:
        return jsonify(error), status

    # Kreiranje korisnika
    hashed_password = sha256_crypt.hash(data['password'])
    user = User(
        forename=data['forename'],
        surname=data['surname'],
        email=data['email'],
        password=hashed_password,
        role='courier'
    )

    database.session.add(user)
    database.session.commit()

    return '', 200

@application.route('/login', methods=['POST'])
def login():
    """
    Prijava korisnika.
    Endpoint: POST /login
    Vraća JWT access token.
    """
    data = request.get_json()

    # 1. Provera email
    if 'email' not in data or not data['email']:
        return jsonify({"message": "Field email is missing."}), 400

    # 2. Provera password
    if 'password' not in data or not data['password']:
        return jsonify({"message": "Field password is missing."}), 400

    # 3. Email format validacija
    if not re.match(EMAIL_REGEX, data['email']):
        return jsonify({"message": "Invalid email."}), 400

    # 4. Provera kredencijala
    user = User.query.filter_by(email=data['email']).first()

    if not user or not sha256_crypt.verify(data['password'], user.password):
        return jsonify({"message": "Invalid credentials."}), 400

    # Kreiranje JWT tokena
    additional_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [user.role],  # Lista sa jednom ulogom
        "type": "access"
    }

    access_token = create_access_token(
        identity=user.email,
        additional_claims=additional_claims
    )

    return jsonify({"accessToken": access_token}), 200

@application.route('/delete', methods=['POST'])
@jwt_required()
def delete_user():
    """
    Brisanje korisničkog naloga.
    Endpoint: POST /delete
    Zahteva JWT token u Authorization header-u.
    """
    # Izvlačenje email-a iz JWT tokena
    claims = get_jwt()
    email = claims['sub']  # 'sub' (subject) sadrži identity iz create_access_token

    # Pronalaženje korisnika
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "Unknown user."}), 400

    # Brisanje korisnika
    database.session.delete(user)
    database.session.commit()

    return '', 200

# Inicijalizacija baze i owner naloga
def initialize_database():
    """
    Kreira tabele i dodaje default owner korisnika.
    Poziva se pri pokretanju aplikacije.
    """
    database.create_all()

    # Provera da li owner već postoji
    owner = User.query.filter_by(email='onlymoney@gmail.com').first()

    if not owner:
        # Kreiranje default owner-a
        owner = User(
            forename='Scrooge',
            surname='McDuck',
            email='onlymoney@gmail.com',
            password=sha256_crypt.hash('evenmoremoney'),
            role='owner'
        )
        database.session.add(owner)
        database.session.commit()
        print("[OK] Default owner kreiran: onlymoney@gmail.com")

# Inicijalizacija baze ODMAH pri importu modula (pre debug reloader-a)
with application.app_context():
    initialize_database()

if __name__ == '__main__':
    # Pokretanje Flask aplikacije
    application.run(debug=True, host='0.0.0.0', port=5000)
