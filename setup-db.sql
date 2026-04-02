CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- Admin Users Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

-- Register default admin: username=admin, password=admin
-- (Note: 'pbkdf2:sha256:600000$A9xYdO4L$8b577bd9192461abfdcc2c1ee3544f8087fc7fb2bbf9faeca3eeacbbfcf58fb1' is werkzeug hash for 'admin')
INSERT IGNORE INTO admins (username, password_hash)
VALUES ('admin', 'scrypt:32768:8:1$K5jL5mH9$cba5da5cd8f1df464ee8fccd3df1a1bd2e71afca311548e65384af3f3db3e6c0');

-- Books Table
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Members Table
CREATE TABLE IF NOT EXISTS members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registered_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issues Table
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
