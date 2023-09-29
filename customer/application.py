
from flask import Flask, request, Response, jsonify
from email.utils import parseaddr
from sqlalchemy import and_ 
from models import Product, Category, ProductCategory, Order, OrderProduct, database
from configuration import Configuration
from flask_jwt_extended import JWTManager, get_jwt, jwt_required
import io
import re
import csv
from web3 import Web3
from web3 import Account
import math
import json
from web3.exceptions import ContractLogicError
import traceback
import logging
import os
CUSTOMER_PORT = 5002

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

ownerAddress = web3.eth.accounts[0]
ShopContract = web3.eth.contract(abi = abi, bytecode = bytecode)

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return jsonify({"msg" : "Missing Authorization Header"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({"msg" : "Unknown user."}), 400


@application.route("/search", methods = ["GET"])
@jwt_required()
def search():
    token = get_jwt()
    role = token["role"]
    if role != "customer":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    productName = request.args.get("name")
    if productName is None:
        productName = ""
    
    categoryName = request.args.get("category")
    if categoryName is None:
        categoryName = ""

    productsSearch = Product.query.filter(Product.name.like(f"%{productName}")).filter(Product.categories.any(Category.name.like(f"%{categoryName}"))).all()
    # productsSearch = Product.query.filter(Product.name.like(f"%{productName}")).all()
    # categoriesSearch = Category.query.filter(Category.name.like(f"%{categoryName}")).all()
    categoriesSearch = Category.query.filter(Category.name.like(f"%{categoryName}")).filter(Category.products.any(Product.name.like(f"%{productName}"))).all()
    products = set()
    categories =set()
    '''
    for product in productsSearch:
    for category in product.categories:
        if category in categoriesSearch:
            products.add(product)
            categories.add(category)
    '''

    [products.add(pr) for pr in productsSearch]
    [categories.add(ct) for ct in categoriesSearch]

    response = { 
        'categories' : [],
        'products' : []
    }

    for product in products:
        id = product.id
        name = product.name
        price = product.price
        productCategories = product.categories
        
        categoriesNames = [category.name for category in productCategories]
        response["products"].append({
            "categories" : categoriesNames,
            "id" : id,
            "name" : name,
            "price" : price
        })

    for category in categories:
        response["categories"].append(category.name)
    
    
    return jsonify(response), 200

@application.route("/order", methods = ["POST"])
@jwt_required()
def order():
    token = get_jwt()
    role = token["role"]
    if role != "customer":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    email = token["sub"]
    requests = request.json.get("requests")
    if requests is None:
        return jsonify({"message" : "Field requests is missing."}), 400
    
    for index, req in enumerate(requests):
        if not "id" in req:
            return jsonify({"message" : f"Product id is missing for request number {index}."}), 400
        if not "quantity" in req:
            return jsonify({"message" : f"Product quantity is missing for request number {index}."}), 400

        try:
            id = int(req["id"])
            if id < 0:
                raise ValueError()
        except ValueError:
            return jsonify({"message" : f"Invalid product id for request number {index}."}), 400

        try:
            quantity = int(req["quantity"])
            if quantity < 0:
                raise ValueError()
        except ValueError:
            return jsonify({"message" : f"Invalid product quantity for request number {index}."}), 400

        product = Product.query.filter(Product.id == id).first()
        if not product:
            return jsonify({"message" : f"Invalid product for request number {index}."}), 400
    
    customerAddress = request.json.get("address")
    if customerAddress is None:
        return jsonify({"message" : "Field address is missing."}), 400
    
    if len(customerAddress) == 0:
        return jsonify({"message" : "Field address is missing."}), 400
    
    if not web3.is_address(customerAddress):
        return jsonify({"message" : "Invalid address."}), 400
    
    order = Order(
        status = "CREATED",
        price = 0 ,
        email = email,
        contractaddress = ""
    )

    database.session.add(order)
    database.session.commit()

    sumPrice = 0
    for index, req in enumerate(requests):
        productId = req["id"]
        quantity = int(req["quantity"])
        
        product = Product.query.filter(Product.id == productId).first()
        print(product.price)
        sumPrice += product.price * quantity
        orderProduct = OrderProduct(
            orderId = order.id,
            productId = productId,
            quantity = quantity
        )
        database.session.add(orderProduct)
        database.session.commit()
    order.price = sumPrice
    database.session.commit()
    print("Adres korisnika --- "  + customerAddress)

    transactionHash = ShopContract.constructor(math.ceil(sumPrice), customerAddress, ownerAddress).transact({
        "from" : ownerAddress,
        'nonce' : web3.eth.get_transaction_count(ownerAddress),
        'gasPrice' : 21000
    })
    
    receipt = web3.eth.wait_for_transaction_receipt(transactionHash)
    contractAddress = receipt.contractAddress
    order.contractaddress = contractAddress
    database.session.commit()

    return jsonify({"id" : order.id }), 200

@application.route("/status", methods = ["GET"])
@jwt_required()
def status():
    token = get_jwt()
    role = token["role"]
    if role != "customer":
        return jsonify({"msg" : "Missing Authorization Header"}), 401
    
    email = token["sub"]
    orders = Order.query.filter(Order.email == email).all()
    
    response = {
        "orders" : []
    }

    for order in orders:
        products = order.products
        items = {
            "products" : [],
            "price" : order.price,
            "status" : order.status,
            "timestamp" : order.timestamp
        }

        for product in products:
            orderProduct = OrderProduct.query.filter(and_(
                OrderProduct.orderId == order.id, 
                OrderProduct.productId == product.id
            )).first()

            item = {
                "categories" : [cat.name for cat in product.categories],
                "name" : product.name,
                "price" : product.price,
                "quantity" : orderProduct.quantity
            }
            items["products"].append(item)

        response["orders"].append(items)
    return jsonify(response), 200

@application.route("/delivered", methods = ["POST"])
@jwt_required()
def delivered():
    token = get_jwt()
    role = token["role"]
    if role != "customer":
        return jsonify({"msg" : "Missing Authorization Header"}), 401

    email = token["sub"]
    data = request.get_json()
    
    print("Ovo mi je prosledjeno")
    print(data)
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
        
        if order.status != "PENDING":
            raise ValueError() 
    except ValueError:
        return jsonify({"message" : "Invalid order id."}), 400
    
    if "keys" not in data:
        return jsonify({"message" : "Missing keys."}), 400
    
    keys = data["keys"]

    if len(keys) == 0:
        return jsonify({"message" : "Missing keys."}), 400
    
    if "passphrase" not in data:
        return jsonify({"message" : "Missing passphrase."}), 400
    
    passphrase = data["passphrase"]

    if len(passphrase) == 0:
        return jsonify({"message" : "Missing passphrase."}), 400
    
    keys = None
    try:
        keys = data["keys"].replace("'", '"')
        keys = json.loads(keys)
    except:
        return jsonify({"message" : "Invalid credentials."}), 400
    
    try:
        customerAddress = web3.to_checksum_address(keys["address"])
        privateKey = Account.decrypt(keys, passphrase).hex()
    except:
        return jsonify({"message" : "Invalid credentials."}), 400
    

    order = Order.query.filter(Order.id == id).first()
    abi = read_file("./solidity/output/MyContract.abi")
    contractaddress = order.contractaddress
    contract = web3.eth.contract(address = contractaddress, abi = abi)

    print("Adresa korisnika iz fajla:", end=" ")
    print(customerAddress)
    # prebaci novac owneru i couireru
    try:
        print("Adresa korisnika iz ugovora:", end=" ")
        print(contract.functions.getCustomerAddress().call())
    except:
        pass
    try:
        transaction = contract.functions.transferFromContract().build_transaction({
            'from': customerAddress,
            'nonce' : web3.eth.get_transaction_count(customerAddress),
            'gasPrice': 21000,
        })
        signed_transcation = web3.eth.account.sign_transaction(transaction, private_key=privateKey)
        transaction_hash = web3.eth.send_raw_transaction(signed_transcation.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
    except ContractLogicError as error:
        msg = error.message
        print(msg)
        msg = msg.replace("execution reverted: VM Exception while processing transaction: revert ", "")
        print (error)
        return jsonify({"message" : msg}), 400
    except Exception as ex:
        error_message = str(ex)

        return jsonify({"message" : error_message}), 400
    


    order = Order.query.filter(Order.id == id).first()
    order.status = 'COMPLETE'
    database.session.commit()
    return Response(status = 200)

@application.route("/pay", methods = ["POST"])
@jwt_required()
def proba():
    token = get_jwt()
    role = token["role"]
    if role != "customer":
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
    except ValueError:
        return jsonify({"message" : "Invalid order id."}), 400
    
    if "keys" not in data:
        return jsonify({"message" : "Missing keys."}), 400
    keys = data["keys"]
    if len(keys) == 0:
        return jsonify({"message" : "Missing keys."}), 400
    
    if "passphrase" not in data:
        return jsonify({"message" : "Missing passphrase."}), 400
    passphrase = data["passphrase"]
    if len(passphrase) == 0:
        return jsonify({"message" : "Missing passphrase."}), 400
    
    keys = None
    try:
        keys = json.loads(data["keys"])
    except:
        return jsonify({"message" : "Invalid credentials."}), 400
    
    try:
        customerAddress = web3.to_checksum_address(keys["address"])
        privateKey = Account.decrypt( keys,passphrase).hex()
    except:
        return jsonify({"message" : "Invalid credentials."}), 400
    
    order = Order.query.filter(Order.id == id).first()
    orderPrice = math.ceil(order.price)
    customerBalance = web3.eth.get_balance(customerAddress)

    if customerBalance < orderPrice:
        return jsonify({"message" : "Insufficient funds."}), 400
    
    try:
        contractaddress = order.contractaddress
        contract = web3.eth.contract(address=contractaddress, abi = abi)

        transcation = contract.functions.setPayment().build_transaction({
            "from" : customerAddress,
            "nonce" : web3.eth.get_transaction_count(customerAddress),
            "gasPrice" : 21000,
            "value" : math.ceil(orderPrice)
        })

        signedTransaction = web3.eth.account.sign_transaction(transcation, privateKey)
        transactionHash = web3.eth.send_raw_transaction(signedTransaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash = transactionHash)
        return Response(status = 200)
    except ContractLogicError as e:
        print(e)
        return jsonify({"message" : "Transfer already complete."}), 400
    except:
        logging.error(traceback.format_exc())
        return jsonify({"message" : "Nesto drugo je bacilo error"}), 400
    

if __name__ == "__main__":
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = CUSTOMER_PORT)