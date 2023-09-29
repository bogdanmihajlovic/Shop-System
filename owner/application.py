import json
import subprocess
from flask import Flask, request, Response, jsonify
from models import Product, Category, ProductCategory, database
from configuration import Configuration
from flask_jwt_extended import JWTManager, get_jwt, jwt_required
import io
import csv
import os
import xmlrpc.client

OWNER_PORT = 5001

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)
clientUrl = os.environ["SPARK_URL"] if ("SPARK_URL" in os.environ) else "127.0.0.1"
print(clientUrl)
client = xmlrpc.client.ServerProxy(f"http://{clientUrl}:8000/")

ganacheUrl = os.environ["GANACHE_URL"] if ("GANACHE_URL" in os.environ) else "127.0.0.1"

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return jsonify({"msg" : "Missing Authorization Header"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({"msg" : "Unknown user."}), 400

@application.route("/update", methods = [ "POST" ])
@jwt_required()
def update():
    token = get_jwt()
    role = token["role"]
    if role != "owner":
        return jsonify({"msg" : "Missing Authorization Header"}), 401

    if not "file" in request.files:
        return jsonify({ "message" : "Field file is missing."}), 400
    
    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream, delimiter=",")

    products = []
    
    for line, row in enumerate(reader):
        if len(row) != 3:
            return jsonify({ "message" : f"Incorrect number of values on line {line}."}), 400
        
        categories = row[0].split("|")
        name = row[1]
        try:
            price = float(row[2])
            if price <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({ "message" : f"Incorrect price on line {line}."}), 400
        
        product = Product.query.filter(Product.name == name).first()
        if product:
            return jsonify({ "message" : f"Product {name} already exists."}), 400
        
        product = Product(name = name, price = price)

        products.append([])
        # products = [ [product0, categories], [product1, categories] ]
        products[line].append(product)
        products[line].append([])

        

        [ products[line][1].append(name) for name in categories ]

    for elem in products:
        product = elem[0]
        categories = elem[1]
        
        database.session.add(product)
        database.session.commit()

        for categoryName in categories:
            category = Category.query.filter(Category.name == categoryName).first()
            if not category:
                category = Category(name = categoryName)
                database.session.add(category)
                database.session.commit()

            productCategory = ProductCategory(productId = product.id, categoryId = category.id)
            database.session.add(productCategory)
            database.session.commit()
        
    
    return Response(status = 200)

@application.route("/category_statistics", methods = ["GET"])
@jwt_required()
def category_statistics():
    token = get_jwt()
    role = token["role"]
    if role != "owner":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    res = client.category()
    return jsonify(res)

@application.route("/product_statistics", methods = ["GET"])
@jwt_required()
def product_statistics():
    token = get_jwt()
    role = token["role"]
    if role != "owner":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    res = client.product()
    return jsonify(res)

if __name__ == "__main__":
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = OWNER_PORT)