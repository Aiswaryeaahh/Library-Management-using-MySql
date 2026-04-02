# Library Management System

A full-stack Library Management System built with Python Flask, MySQL, and modern Vanilla HTML/CSS/JS.

## Features

- **Book Management**: Add, edit, delete books, search by title/author.
- **Member Management**: Register new library members.
- **Issues & Returns**: Issue books to members, track due dates, and return books.
- **Dashboard**: High-level statistics of books, members, and active loans.
- **Authentication**: Simple admin login system.

## Tech Stack

- **Backend**: Python 3.x with Flask
- **Database**: MySQL Server
- **Frontend**: Plain HTML5, CSS3, JavaScript (ES6+), Inter Font

## Prerequisites

- [Python 3.x](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)

## Installation & Setup

1. **Clone/Download the repository** to your local machine.
2. **Setup virtual environment and install dependencies**:
   ```bash
   python -m venv venv
   # Activate on Windows:
   .\venv\Scripts\activate
   # Activate on macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```
3. **Database Configuration**:
   - Ensure you have a local MySQL server running.
   - The `.env` file contains the default configuration:
     ```
     DB_HOST=localhost
     DB_USER=root
     DB_PASS=
     DB_NAME=library_db
     ```
   - *Modify `.env` if your MySQL root has a different password!*

4. **Initialize Database Schema**:
   Run the initialization script which automatically reads `setup-db.sql` and sets up the tables and default admin account.
   ```bash
   python init_db.py
   ```

5. **Start the Flask Application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   Open a web browser and go to `http://127.0.0.1:5000`
   
   **Default Login Credentials**:
   - Username: `admin`
   - Password: `admin`

## SQL Schema Generation (Manual Alternative)

If you prefer to set up the database manually, you can log into your MySQL shell:
```bash
mysql -u root -p
```
And execute the contents of `setup-db.sql`:
```bash
source path/to/project/setup-db.sql
```
