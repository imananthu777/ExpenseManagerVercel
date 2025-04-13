from flask import Flask, render_template, request, redirect, url_for, session
import hashlib
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key!

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_string(text):
    return hashlib.sha256(str(text).encode()).hexdigest()

def encrypt_mobile(mobile):
    return hash_string(mobile)[:12]  # Take first 12 chars of hash for shorter id

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        users = load_users()
        encrypted_mobile = encrypt_mobile(mobile)
        if encrypted_mobile in users and users[encrypted_mobile]['password'] == hash_string(password):
            session['logged_in'] = True
            session['mobile'] = encrypted_mobile #Store encrypted mobile in session
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

        users = load_users()
        encrypted_mobile = encrypt_mobile(mobile)
        if encrypted_mobile in users:
            return "Mobile number already registered!"

        users[encrypted_mobile] = {
            'password': hash_string(password),
            'name': name,
            'email': email
        }
        save_users(users)

        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/welcome')
def welcome():
    if session.get('logged_in'):
        encrypted_mobile = session.get('mobile')
        users = load_users()
        user = users.get(encrypted_mobile, {})
        return f"Welcome {user.get('name')}! You are logged in."
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)