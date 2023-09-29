from flask import Flask, request, Response, jsonify
from email.utils import parseaddr
from sqlalchemy import and_
from models import User, database
from configuration import Configuration
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required
from decorater import token_check

import re
PASSWORD_MIN_LEN = 8
AUTHENTICATION_PORT = 5000

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return jsonify({"msg" : "Missing Authorization Header"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({"msg" : "Unknown user."}), 400

@application.route("/test", methods = ["GET"])
def testConnection():
    return str(User.query.all())

@application.route("/register_customer", methods = ["POST"])
def register_customer():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    
    # check for errors
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    
    response = {
        'message' : ''
    }
    
    if forenameEmpty:
        response["message"] = "Field forename is missing."
        return jsonify(response), 400
    elif surnameEmpty:
        response["message"] = "Field surname is missing."
        return jsonify(response), 400
    elif emailEmpty:
        response["message"] = "Field email is missing."
        return jsonify(response), 400
    elif passwordEmpty:
        response["message"] = "Field password is missing."
        return jsonify(response), 400

    
    if not re.match(r"[^@]+@[^@]+\.com$", email):  
        response["message"] = "Invalid email."
        return jsonify(response), 400

    if len(password) < PASSWORD_MIN_LEN:
        response["message"] = "Invalid password."
        return jsonify(response), 400
    
    user = User.query.filter(and_(User.email == email)).first()
    if user:
        response["message"] = "Email already exists."
        return jsonify(response), 400
    
    # create new user 
    user = User(
        forename = forename, 
        surname = surname, 
        email = email, 
        password = password,
        role = "customer"
    )

    database.session.add(user)
    database.session.commit()

    #role = Role.query.filter(and_(Role.name == "customer")).first()
    #userRole = UserRole(userId = user.id, roleId = role.id)
    
    #database.session.add(userRole)
    #database.session.commit()
    
    return Response(status=200)

@application.route("/register_courier", methods = ["POST"])
def register_courier():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    
    # check for errors
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    
    response = {
        'message' : ''
    }
    
    if forenameEmpty:
        response["message"] = "Field forename is missing."
        return jsonify(response), 400
    elif surnameEmpty:
        response["message"] = "Field surname is missing."
        return jsonify(response), 400
    elif emailEmpty:
        response["message"] = "Field email is missing."
        return jsonify(response), 400
    elif passwordEmpty:
        response["message"] = "Field password is missing."
        return jsonify(response), 400

    if not re.match(r"[^@]+@[^@]+\.com$", email):  
        response["message"] = "Invalid email."
        return jsonify(response), 400

    if len(password) < PASSWORD_MIN_LEN:
        response["message"] = "Invalid password."
        return jsonify(response), 400
    
    user = User.query.filter(and_(User.email == email)).first()
    if user:
        response["message"] = "Email already exists."
        return jsonify(response), 400
    
    # create new user 
    user = User(
        forename = forename, 
        surname = surname,
        email = email,
        password = password,
        role = "courier"
    )

    database.session.add(user)
    database.session.commit()

    #role = Role.query.filter(and_(Role.name == "courier")).first()
    #userRole = UserRole(userId = user.id, roleId = role.id)
    
    #database.session.add(userRole)

    return Response(status=200)   

jwt = JWTManager(application)

@application.route("/login", methods = ["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    response = {
        'message' : ''
    }

    if emailEmpty:
        response["message"] = "Field email is missing."
        return jsonify(response), 400
    elif passwordEmpty:
        response["message"] = "Field password is missing."
        return jsonify(response), 400
        
    if not re.match(r"[^@]+@[^@]+\.com$", email):  
        response["message"] = "Invalid email."
        return jsonify(response), 400
    
    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        response["message"] = "Invalid credentials."
        return jsonify(response), 400
    
    additionalClaims = {
        "forename" : user.forename,
        "surname" : user.surname,
        "password" : user.password,
        "role" : user.role
    }

    accessToken = create_access_token(identity = user.email, additional_claims = additionalClaims)
    #refreshToken = create_refresh_token(identity = user.email, additional_claims = additionalClaims)
    
    return jsonify({ "accessToken" : accessToken}), 200

@application.route("/check", methods = ["POST"])
@jwt_required()
def check():
    return "Token is valid"

@application.route("/delete", methods = ["POST"])
@token_check
def delete(user):
    database.session.delete(user)
    database.session.commit()
    return Response(status = 200)

if __name__ == "__main__":
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = AUTHENTICATION_PORT)
