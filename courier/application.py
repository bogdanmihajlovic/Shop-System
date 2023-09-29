from flask import Flask, request, Response, jsonify
from email.utils import parseaddr
from sqlalchemy import and_ 
from models import Product, Category, ProductCategory, Order, OrderProduct, database
from configuration import Configuration
from flask_jwt_extended import JWTManager, get_jwt, jwt_required
from web3 import Web3
import io
import re
import csv
import os

COURIER_PORT = 5003

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )
    
ganacheUrl = os.environ["GANACHE_URL"] if ("GANACHE_URL" in os.environ) else "127.0.0.1"
web3 = Web3(Web3.HTTPProvider(f"http://{ganacheUrl}:8545"))

abi = read_file("./solidity/output/MyContract.abi")
bytecode = read_file("./solidity/output/MyContract.bin")
ShopContract = web3.eth.contract(abi = abi, bytecode = bytecode)

ownerAddress = web3.eth.accounts[0]
couirerAddress = web3.eth.accounts[1]

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return jsonify({"msg" : "Missing Authorization Header"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({"msg" : "Unknown user."}), 400


@application.route("/orders_to_deliver", methods = ["GET"])
@jwt_required()
def search():
    token = get_jwt()
    role = token["role"]
    if role != "courier":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    response = {
        "orders" : []
    }

    orders = Order.query.filter(Order.status == "CREATED").all()
    for order in orders:
        response["orders"].append({
            "id" : order.id,
            "email" : order.email
        })
    
    return jsonify(response), 200

@application.route("/pick_up_order", methods = ["POST"])
@jwt_required()
def deliver():
    token = get_jwt()
    role = token["role"]
    if role != "courier":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"message" : "Missing order id."}), 400
    
    if "id" not in data:
        return jsonify({"message" : "Missing order id."}), 400
    
    id = data["id"]
    try:
        id = int(id)

        if id < 0:
            raise ValueError()
        
        order = Order.query.filter(Order.id == id).first()
        if not order:
            raise ValueError()
        
        if order.status != "CREATED":
            raise ValueError() 
    except ValueError:
        return jsonify({"message" : "Invalid order id."}), 400
    
    if "address" not in data:
        return jsonify({"message" : "Missing address."}), 400
    
    couirerAddress = data["address"]

    if len(couirerAddress) == 0:
        return jsonify({"message" : "Missing address."}), 400
    
    if not web3.is_address(couirerAddress):
        return jsonify({"message" : "Invalid address."}), 400
    

    order = Order.query.filter(Order.id == id).first()
    contractaddress = order.contractaddress
    orderPrice = order.price
    
    contract = web3.eth.contract(address=contractaddress, abi = abi)
    if contract.functions.getPayment().call() < orderPrice:
        return jsonify({"message" : "Transfer not complete."}), 400
    
    # customerAddress = contract.functions.getCustomerAddress().call()

    contract.functions.setCourierAddress(couirerAddress).transact({
        'from' : ownerAddress,
        'nonce' : web3.eth.get_transaction_count(ownerAddress),
        'gasPrice' : 21000
    })

    order.status = "PENDING"
    database.session.commit()
    
    return Response(status = 200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = COURIER_PORT)