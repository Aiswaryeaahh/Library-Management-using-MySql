from db_config import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()
new_hash = 'scrypt:32768:8:1$ktyj1FIydnrcEPHu$c9725e31199b841f98375bc64c62928a87bcb87559128b51bf37a78da500840573f0fea67e987d05bead454a52c3a5e93a743c71279457b8dc1fc2886aa8c611'
cursor.execute("UPDATE admins SET password_hash = %s WHERE username = 'admin'", (new_hash,))
conn.commit()
cursor.close()
conn.close()
print("Admin password updated")
