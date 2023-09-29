from functools import wraps
from flask import request, jsonify, current_app
import jwt
from sqlalchemy import and_
from models import User

def token_check(function):
    @wraps(function)
    def decorator():
        if not "Authorization" in request.headers:
            return jsonify({"msg" : "Missing Authorization Header"}), 401

        accessToken = request.headers["Authorization"].split(" ")[-1]

        try:
            data = jwt.decode(accessToken, current_app.config["JWT_SECRET_KEY"], algorithms = ["HS256"])
            
            email = data["sub"]
            surname = data["surname"]
            forename = data["forename"]

            user = User.query.filter(and_(User.email == email, User.surname == surname, User.forename == forename)).first()
            if not user:
                return jsonify({"message" : "Unknown user."}), 400
            
            return function(user)
        except Exception:
            return {
                "message" : "Access token expired."
            }
    
    return decorator
