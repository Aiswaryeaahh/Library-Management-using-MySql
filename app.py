import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
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

# ==================== GUI Routes ====================

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
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['logged_in'] = True
            session['username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!")
            return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# ==================== User Routes ====================

@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if email exists
        cursor.execute("SELECT id FROM members WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered!")
            cursor.close()
            conn.close()
            return render_template('user_register.html', error="Email already registered")
        
        # Insert new member
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO members (name, email, phone, registered_date, password_hash) VALUES (%s, %s, %s, CURDATE(), %s)",
            (name, email, phone, password_hash)
        )
        member_id = cursor.lastrowid
        membership_id = f"MEM{member_id:04d}"
        cursor.execute("UPDATE members SET membership_id=%s WHERE id=%s", (membership_id, member_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Registration successful! Please login.")
        return redirect(url_for('user_login'))
    
    return render_template('user_register.html')

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
        
        if member and check_password_hash(member['password_hash'], password):
            session['user_logged_in'] = True
            session['user_id'] = member['id']
            session['user_name'] = member['name']
            session['membership_id'] = member['membership_id']
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials!")
            return render_template('user_login.html', error="Invalid credentials")
            
    return render_template('user_login.html')

@app.route('/user/logout')
def user_logout():
    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('membership_id', None)
    return redirect(url_for('user_login'))

@app.route('/user/dashboard')
@user_login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/user/search', methods=['GET', 'POST'])
@user_login_required
def user_search():
    if request.method == 'POST':
        search = request.form.get('search', '')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if search:
            query = "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s AND available_copies > 0"
            cursor.execute(query, (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute("SELECT * FROM books WHERE available_copies > 0")
            
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('user_search.html', books=books, search=search)
    
    return render_template('user_search.html')

@app.route('/user/borrow/<int:book_id>', methods=['POST'])
@user_login_required
def user_borrow(book_id):
    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # check availability
        cursor.execute("SELECT available_copies FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        
        if not book or book[0] <= 0:
            flash("Book not available!")
            return redirect(url_for('user_search'))
            
        # create issue record
        cursor.execute(
            "INSERT INTO issues (book_id, member_id, issue_date, due_date) VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))",
            (book_id, user_id)
        )
        
        # update available copies
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id=%s", (book_id,))
        
        conn.commit()
        flash("Book borrowed successfully!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/return/<int:issue_id>', methods=['POST'])
@user_login_required
def user_return(issue_id):
    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # verify the issue belongs to user and is issued
        cursor.execute("SELECT book_id, status FROM issues WHERE id=%s AND member_id=%s", (issue_id, user_id))
        issue = cursor.fetchone()
        if not issue or issue[1] == 'returned':
            flash("Invalid return request!")
            return redirect(url_for('user_profile'))
            
        book_id = issue[0]
        
        # update issue status
        cursor.execute("UPDATE issues SET status='returned', return_date=CURDATE() WHERE id=%s", (issue_id,))
        
        # update available copies
        cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id=%s", (book_id,))
        
        conn.commit()
        flash("Book returned successfully!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('user_profile'))

@app.route('/user/profile')
@user_login_required
def user_profile():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get borrowed books
    query = """
    SELECT i.*, b.title, b.author, 
           DATEDIFF(CURDATE(), i.due_date) as days_overdue
    FROM issues i
    JOIN books b ON i.book_id = b.id
    WHERE i.member_id=%s AND i.status='issued'
    """
    cursor.execute(query, (user_id,))
    borrowed = cursor.fetchall()
    
    # Calculate fines
    total_fine = 0
    for book in borrowed:
        if book['days_overdue'] > 0:
            total_fine += book['days_overdue'] * 10  # 10 per day
    
    # Get returned books
    query = """
    SELECT i.*, b.title, b.author, i.return_date,
           CASE WHEN i.return_date > i.due_date THEN DATEDIFF(i.return_date, i.due_date) * 10 ELSE 0 END as fine
    FROM issues i
    JOIN books b ON i.book_id = b.id
    WHERE i.member_id=%s AND i.status='returned'
    ORDER BY i.return_date DESC
    """
    cursor.execute(query, (user_id,))
    returned = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user_profile.html', borrowed=borrowed, returned=returned, total_fine=total_fine)

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

# ==================== API Routes ====================

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT sum(total_copies) as total_books, sum(available_copies) as available_books FROM books")
    books_stat = cursor.fetchone()
    
    cursor.execute("SELECT count(*) as total_members FROM members")
    members_stat = cursor.fetchone()
    
    cursor.execute("SELECT count(*) as active_loans FROM issues WHERE status='issued'")
    loans_stat = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'total_books': books_stat['total_books'] or 0,
        'available_books': books_stat['available_books'] or 0,
        'total_members': members_stat['total_members'] or 0,
        'active_loans': loans_stat['active_loans'] or 0
    })

# --- Book APIs ---
@app.route('/api/books', methods=['GET'])
@login_required
def get_books():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search:
        query = "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s"
        cursor.execute(query, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM books")
        
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(books)

@app.route('/api/books', methods=['POST'])
@login_required
def add_book():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, total_copies, available_copies) VALUES (%s, %s, %s, %s)",
            (data['title'], data['author'], data['total_copies'], data['total_copies']) # assuming new book starts with all copies available
        )
        conn.commit()
        return jsonify({'message': 'Book added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/books/<int:id>', methods=['PUT'])
@login_required
def update_book(id):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # calculate difference in total copies to adjust available copies
        cursor.execute("SELECT total_copies, available_copies FROM books WHERE id=%s", (id,))
        current_book = cursor.fetchone()
        if not current_book:
            return jsonify({'error': 'Book not found'}), 404
            
        diff = int(data['total_copies']) - current_book[0]
        new_available = current_book[1] + diff
        
        cursor.execute(
            "UPDATE books SET title=%s, author=%s, total_copies=%s, available_copies=%s WHERE id=%s",
            (data['title'], data['author'], data['total_copies'], new_available, id)
        )
        conn.commit()
        return jsonify({'message': 'Book updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/books/<int:id>', methods=['DELETE'])
@login_required
def delete_book(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id=%s", (id,))
        conn.commit()
        return jsonify({'message': 'Book deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- Member APIs ---
@app.route('/api/members', methods=['GET'])
@login_required
def get_members():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    
    # Format date for JSON serialization
    for member in members:
        if member['registered_date']:
            member['registered_date'] = member['registered_date'].strftime('%Y-%m-%d')
            
    cursor.close()
    conn.close()
    return jsonify(members)

@app.route('/api/members', methods=['POST'])
@login_required
def add_member():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert NULL for password_hash and membership_id
        cursor.execute(
            "INSERT INTO members (name, email, phone, registered_date, password_hash, membership_id) VALUES (%s, %s, %s, CURDATE(), %s, %s)",
            (data['name'], data['email'], data['phone'], None, None)
        )
        member_id = cursor.lastrowid
        membership_id = f"MEM{member_id:04d}"
        cursor.execute("UPDATE members SET membership_id=%s WHERE id=%s", (membership_id, member_id))
        conn.commit()
        return jsonify({'message': 'Member added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- Issue APIs ---
@app.route('/api/issues', methods=['GET'])
@login_required
def get_issues():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT i.*, b.title as book_title, m.name as member_name 
    FROM issues i
    JOIN books b ON i.book_id = b.id
    JOIN members m ON i.member_id = m.id
    ORDER BY i.issue_date DESC
    """
    cursor.execute(query)
    issues = cursor.fetchall()
    
    # Format dates
    for issue in issues:
        issue['issue_date'] = issue['issue_date'].strftime('%Y-%m-%d')
        issue['due_date'] = issue['due_date'].strftime('%Y-%m-%d')
        if issue['return_date']:
            issue['return_date'] = issue['return_date'].strftime('%Y-%m-%d')
            
    cursor.close()
    conn.close()
    return jsonify(issues)

@app.route('/api/issues', methods=['POST'])
@login_required
def issue_book():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # check availability
        cursor.execute("SELECT available_copies FROM books WHERE id=%s", (data['book_id'],))
        book = cursor.fetchone()
        
        if not book or book[0] <= 0:
            return jsonify({'error': 'Book not available'}), 400
            
        # create issue record
        cursor.execute(
            "INSERT INTO issues (book_id, member_id, issue_date, due_date) VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))",
            (data['book_id'], data['member_id'])
        )
        
        # update available copies
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id=%s", (data['book_id'],))
        
        conn.commit()
        return jsonify({'message': 'Book issued successfully'}), 201
    except Exception as e:
        conn.rollback() # rollback if any of above fails
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/issues/<int:id>/return', methods=['POST'])
@login_required
def return_book(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # get book id
        cursor.execute("SELECT book_id, status FROM issues WHERE id=%s", (id,))
        issue = cursor.fetchone()
        if not issue or issue[1] == 'returned':
            return jsonify({'error': 'Invalid issue record or already returned'}), 400
            
        book_id = issue[0]
        
        # update issue status
        cursor.execute("UPDATE issues SET status='returned', return_date=CURDATE() WHERE id=%s", (id,))
        
        # update available copies
        cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id=%s", (book_id,))
        
        conn.commit()
        return jsonify({'message': 'Book returned successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
