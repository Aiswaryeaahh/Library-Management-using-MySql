import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv
from functools import wraps
from db_config import get_db_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def user_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ADMIN LOGIN ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE username=%s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and admin['password_hash'] == password:
            session['logged_in'] = True
            session['username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!")
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==================== USER REGISTER ====================

@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM members WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered!")
            cursor.close()
            conn.close()
            return render_template('user_register.html')

        cursor.execute(
            "INSERT INTO members (name, email, phone, registered_date, password) VALUES (%s,%s,%s,CURDATE(),%s)",
            (name, email, phone, password)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please login.")
        return redirect(url_for('user_login'))

    return render_template('user_register.html')


# ==================== USER LOGIN ====================

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM members WHERE email=%s", (email,))
        member = cursor.fetchone()
        cursor.close()
        conn.close()

        if member and member.get('password') == password:
            session['user_logged_in'] = True
            session['user_id'] = member['id']
            session['user_name'] = member['name']
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials!")
            return render_template('user_login.html')

    return render_template('user_login.html')


@app.route('/user/logout')
def user_logout():
    session.clear()
    return redirect(url_for('user_login'))


@app.route('/user/dashboard')
@user_login_required
def user_dashboard():
    return render_template(
        "user_dashboard.html",
        user_name=session.get('user_name')
    )


# ==================== USER SEARCH ====================

@app.route('/user/search', methods=['GET', 'POST'])
@user_login_required
def user_search():
    if request.method == 'POST':
        search = request.form.get('search', '')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if search:
            query = "SELECT * FROM books WHERE (title LIKE %s OR author LIKE %s) AND available_copies > 0"
            cursor.execute(query, (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute("SELECT * FROM books WHERE available_copies > 0")

        books = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('user_search.html', books=books, search=search)

    return render_template('user_search.html')


# ==================== ADMIN PAGES ====================

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')


@app.route('/books')
@login_required
def books_page():
    return render_template('books.html')


@app.route('/members')
@login_required
def members_page():
    return render_template('members.html')


@app.route('/issues')
@login_required
def issues_page():
    return render_template('issues.html')


# ==================== MEMBER API ====================

@app.route('/api/members', methods=['POST'])
@login_required
def add_member():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO members (name, email, phone, registered_date, password) VALUES (%s,%s,%s,CURDATE(),%s)",
            (data['name'], data['email'], data['phone'], "")
        )

        conn.commit()
        return jsonify({'message': 'Member added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.errorhandler(Exception)
def handle_exception(e):
    return str(e), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)