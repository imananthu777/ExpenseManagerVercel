
from flask import Flask, render_template, request, redirect, url_for, session
import hashlib
import os
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key!

def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    return conn

# Create users table if it doesn't exist
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            mobile VARCHAR(15) PRIMARY KEY,
            password VARCHAR(64),
            name VARCHAR(100),
            email VARCHAR(100)
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute('SELECT * FROM users WHERE mobile = %s AND password = %s',
                   (mobile, hash_password(password)))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['mobile'] = mobile
            return redirect(url_for('welcome'))
        
        error = "Invalid mobile number or password. Please try again."
        return render_template('login.html', error=error)

    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']
        email = request.form.get('email', '')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if mobile already exists
        cur.execute('SELECT mobile FROM users WHERE mobile = %s', (mobile,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return "Mobile number already registered!"
        
        # Insert new user
        cur.execute('''
            INSERT INTO users (mobile, password, name, email)
            VALUES (%s, %s, %s, %s)
        ''', (mobile, hash_password(password), name, email))
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('home'))
        
    return render_template('register.html')

@app.route('/welcome')
def welcome():
    if session.get('logged_in'):
        mobile = session.get('mobile')
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute('SELECT name FROM users WHERE mobile = %s', (mobile,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return f"Welcome {user['name']}! You are logged in."
    return redirect(url_for('home'))

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)
