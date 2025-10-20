import re
from flask import request, jsonify
from configuration import application, database
from models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from passlib.hash import sha256_crypt
from sqlalchemy import and_

email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

@application.route('/register_customer', methods=['POST'])
def register_customer():
    req_data = request.get_json()

    if 'forename' not in req_data or not req_data['forename']:
        return jsonify({"message": "Field forename is missing."}), 400

    if 'surname' not in req_data or not req_data['surname']:
        return jsonify({"message": "Field surname is missing."}), 400

    if 'email' not in req_data or not req_data['email']:
        return jsonify({"message": "Field email is missing."}), 400

    if 'password' not in req_data or not req_data['password']:
        return jsonify({"message": "Field password is missing."}), 400

    if not re.match(email_pattern, req_data['email']):
        return jsonify({"message": "Invalid email."}), 400

    if len(req_data['password']) < 8:
        return jsonify({"message": "Invalid password."}), 400

    existing = User.query.filter_by(email=req_data['email']).first()
    if existing:
        return jsonify({"message": "Email already exists."}), 400

    hashed_pw = sha256_crypt.hash(req_data['password'])
    new_user = User(
        forename=req_data['forename'],
        surname=req_data['surname'],
        email=req_data['email'],
        password=hashed_pw,
        role='customer'
    )

    database.session.add(new_user)
    database.session.commit()

    return '', 200

@application.route('/register_courier', methods=['POST'])
def register_courier():
    req_data = request.get_json()

    if 'forename' not in req_data or not req_data['forename']:
        return jsonify({"message": "Field forename is missing."}), 400

    if 'surname' not in req_data or not req_data['surname']:
        return jsonify({"message": "Field surname is missing."}), 400

    if 'email' not in req_data or not req_data['email']:
        return jsonify({"message": "Field email is missing."}), 400

    if 'password' not in req_data or not req_data['password']:
        return jsonify({"message": "Field password is missing."}), 400

    if not re.match(email_pattern, req_data['email']):
        return jsonify({"message": "Invalid email."}), 400

    if len(req_data['password']) < 8:
        return jsonify({"message": "Invalid password."}), 400

    existing = User.query.filter_by(email=req_data['email']).first()
    if existing:
        return jsonify({"message": "Email already exists."}), 400

    hashed_pw = sha256_crypt.hash(req_data['password'])
    new_user = User(
        forename=req_data['forename'],
        surname=req_data['surname'],
        email=req_data['email'],
        password=hashed_pw,
        role='courier'
    )

    database.session.add(new_user)
    database.session.commit()

    return '', 200

@application.route('/login', methods=['POST'])
def login():
    json_data = request.get_json()

    if 'email' not in json_data or not json_data['email']:
        return jsonify({"message": "Field email is missing."}), 400

    if 'password' not in json_data or not json_data['password']:
        return jsonify({"message": "Field password is missing."}), 400

    if not re.match(email_pattern, json_data['email']):
        return jsonify({"message": "Invalid email."}), 400

    user = User.query.filter_by(email=json_data['email']).first()

    if not user or not sha256_crypt.verify(json_data['password'], user.password):
        return jsonify({"message": "Invalid credentials."}), 400

    token_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [user.role],
        "type": "access"
    }

    access_token = create_access_token(
        identity=user.email,
        additional_claims=token_claims
    )

    return jsonify({"accessToken": access_token}), 200

@application.route('/delete', methods=['POST'])
@jwt_required()
def delete_user():
    jwt_data = get_jwt()
    user_email = jwt_data['sub']

    user = User.query.filter_by(email=user_email).first()

    if not user:
        return jsonify({"message": "Unknown user."}), 400

    database.session.delete(user)
    database.session.commit()

    return '', 200

if __name__ == '__main__':
    with application.app_context():
        database.create_all()

        owner = User.query.filter_by(email='onlymoney@gmail.com').first()

        if not owner:
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

    application.run(debug=True, host='0.0.0.0', port=5000)
