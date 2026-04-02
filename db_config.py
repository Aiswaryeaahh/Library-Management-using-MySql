import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    print("DB PASS:", os.getenv("DB_PASS"))
    return mysql.connector.connect(
        host=os.getenv("mysql.railway.internal"),
        user=os.getenv("root"),
        password=os.getenv("okGFRHCeomIcEkyPvOzffVpARFYtxuLX"),
        database=os.getenv("railway"),
        auth_plugin='mysql_native_password'
    )