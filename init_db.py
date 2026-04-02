import mysql.connector

# 1. SETUP CONNECTION
try:
    connection = mysql.connector.connect(
        host="interchange.proxy.rlwy.net",
        user="root",
        password="okGFRHCeomIcEkyPvOzffVpARFYtxuLX",
        database="railway", 
        port=27876
    )
    cursor = connection.cursor()

    # 2. YOUR FINAL SQL SCRIPT (Cleaned)
    sql_script = """
    -- 1. Admin Users Table
    CREATE TABLE IF NOT EXISTS admins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL
    );

    -- 2. Register default admin
    INSERT IGNORE INTO admins (username, password_hash)
    VALUES ('admin', 'scrypt:32768:8:1$K5jL5mH9$cba5da5cd8f1df464ee8fccd3df1a1bd2e71afca311548e65384af3f3db3e6c0');

    -- 3. Books Table
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        total_copies INT NOT NULL DEFAULT 1,
        available_copies INT NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 4. Members Table (This replaces 'users')
    CREATE TABLE IF NOT EXISTS members (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone VARCHAR(20),
        registered_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 5. Issues Table
    CREATE TABLE IF NOT EXISTS issues (
        id INT AUTO_INCREMENT PRIMARY KEY,
        book_id INT NOT NULL,
        member_id INT NOT NULL,
        issue_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE NULL,
        status ENUM('issued', 'returned') DEFAULT 'issued',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
    );
    """

    # 3. EXECUTE
    for result in cursor.execute(sql_script, multi=True):
        pass

    connection.commit()
    print("🚀 Success! Your Library database is now ready in Railway.")

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()