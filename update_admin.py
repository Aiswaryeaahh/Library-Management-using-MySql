from db_config import get_db_connection
from werkzeug.security import generate_password_hash

conn = get_db_connection()
cursor = conn.cursor()
new_hash = generate_password_hash('admin')
cursor.execute("UPDATE admins SET password_hash = %s WHERE username = 'admin'", (new_hash,))
conn.commit()
cursor.close()
conn.close()
print("Admin password updated")