from pyspark.sql import SparkSession
from pyspark.sql.functions import count, col, coalesce, when
from xmlrpc.server import SimpleXMLRPCServer
import json
import os

DATABASE_IP = os.environ["DATABASE_IP"] if ( "DATABASE_IP" in os.environ ) else "localhost"
        
def product():
    print("Zahtev primljen")
    PRODUCTION = True if ( "PRODUCTION" in os.environ ) else False

    if ( not PRODUCTION ):
        builder.master ( "local[*]" )

    builder = SparkSession.builder.appName ( "Simple PySpark" ) 
    spark = builder.getOrCreate ( )
    
    products= spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.products" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    orders = spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.orders" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    order_products = spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.orderproduct" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    orders = orders.drop("contractaddress")

    print("Ispisujem procitano")
    # orders.show()
    # orders.show()
    # order_products.show()
    
    joined_data = order_products.join(orders, order_products.orderId == orders.id)\
        .join(products, order_products.productId == products.id)
    
    
    sold_orders = joined_data.filter(joined_data.status == "COMPLETE")
    waiting_orders = joined_data.filter(joined_data.status != "COMPLETE")
    
    print("pre sabiranja sold")
    sold_orders = sold_orders.groupBy("name").sum("quantity")
    sold_orders = sold_orders.withColumnRenamed("sum(quantity)", "quantity")
    
    print("pre sabiranja waiting")
    waiting_orders = waiting_orders.groupBy("name").sum("quantity")
    waiting_orders = waiting_orders.withColumnRenamed("sum(quantity)", "quantity")

    out = {
        "statistics" : []
    }
    print("stampannje sold_orders")
    #soldDict = sold_orders.rdd.collectAsMap()
    sold_orders.show()
    print("pretvaranje u recnik")
    soldDict = sold_orders.rdd.collectAsMap()
    waitingDict = waiting_orders.rdd.collectAsMap()
    finalDict = {}
    print("ispisujem soldDict")
    #print(soldDict)
    print("ispisujem waitingDict")
    #print(waitingDict)
    print("krecem sa spajanjem")

    for name in soldDict:
        sold = soldDict[name]
        waiting = 0
        if name in waitingDict:
            waiting = waitingDict[name]
        finalDict[name] = [sold, waiting]
    
    for name in waitingDict:
        waiting = waitingDict[name]
        sold = 0
        if name not in finalDict:
            finalDict[name] = [sold, waiting]
    
    for name in finalDict:
        sold = finalDict[name][0]
        waiting = finalDict[name][1]

        elem = {
            "name" : name,
            "sold" : sold,
            "waiting" : waiting
        }
        out["statistics"].append(elem)

    spark.stop()
    return out

def category():
    print("Zahtev primljen")
    PRODUCTION = True if ( "PRODUCTION" in os.environ ) else False

    if ( not PRODUCTION ):
        builder.master ( "local[*]" )

    builder = SparkSession.builder.appName ( "Simple PySpark" ) 
    spark = builder.getOrCreate ( )
    
    products= spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.products" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    
    orders = spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.orders" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    order_products = spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.orderproduct" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    product_category = spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.productcategory" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    categories = spark.read \
        .format ( "jdbc" ) \
        .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
        .option ( "url", f"jdbc:mysql://{DATABASE_IP}:3306/shop" ) \
        .option ( "dbtable", "shop.categories" ) \
        .option ( "user", "root" ) \
        .option ( "password", "root" ) \
        .load ( )
    
    orders = orders.drop("contractaddress")
    orders = orders.filter(col("status") == "COMPLETE")
    categories_count = orders\
        .join(order_products, orders.id == order_products.orderId)\
        .join(product_category, product_category.productId == order_products.productId)\
        .join(categories, categories.id == product_category.categoryId)\
        .groupBy(categories.name)\
        .sum("quantity")
    
    data = categories.join(categories_count, categories.name == categories_count.name, "left")
    data = data.fillna(0)
    print("KATEGORIJA")
    #data.show()
    result = data.rdd.flatMap(lambda x : x).collect()
    for res in result:
        print(res, end=" tip")
        print(type(res))

    out = []
    for i in range(0, len(result), 4):
        name = result[i + 1]
        count = result[i + 3]
        if(count is None):
            count = 0
        out.append([name, count])

    out.sort(key=lambda x: (-x[1], x[0]))

    jsonOut = {
        "statistics" : []
    }
    [ jsonOut["statistics"].append(x[0]) for x in out]
    

    spark.stop()
    return jsonOut

def slovo():
    return ["Yeste", "Nije"]

server = SimpleXMLRPCServer(('0.0.0.0', 8000))
server.register_function(product, 'product')
server.register_function(category, 'category')
server.register_function(slovo, 'slovo')

print("Server pokrenut")
server.serve_forever()