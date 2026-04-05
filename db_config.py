import os
import mysql.connector
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Parse DATABASE_URL (e.g., mysql://user:pass@host:port/db)
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
            port=port,
            auth_plugin='mysql_native_password'
        )
    else:
        # Fallback to individual env vars
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            auth_plugin='mysql_native_password'
        )