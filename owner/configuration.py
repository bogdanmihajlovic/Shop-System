from datetime import timedelta
import os

url = os.environ["DATABASE_URL"] if ("DATABASE_URL" in os.environ) else ""
databaseUrl = f"mysql+pymysql://root:root@{url}/shop" if len(url) \
    else "mysql+pymysql://root:root@localhost:3307/shop"

class Configuration():
    SQLALCHEMY_DATABASE_URI = databaseUrl
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours = 1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours = 1)