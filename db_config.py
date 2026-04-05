import os
import mysql.connector
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    # If DATABASE_URL is provided (preferred for Vercel)
    if database_url:
        parsed = urlparse(database_url)
        host = parsed.hostname
        user = parsed.username
        password = parsed.password
        database = parsed.path.lstrip('/')
        port = parsed.port or 3306

        return mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port),
            auth_plugin='mysql_native_password'
        )

    # Otherwise use individual environment variables
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", 3306)

    if not (host and user and password and database):
        raise ValueError(
            "Missing database environment variables. "
            "Set DATABASE_URL or DB_HOST, DB_USER, DB_PASS, DB_NAME in Vercel."
        )

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=int(port),
        auth_plugin='mysql_native_password'
    )