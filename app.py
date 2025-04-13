from flask import Flask, render_template, request, redirect, url_for, session, make_response
import hashlib
import json
import os
from datetime import datetime
from pytz import timezone
import pandas as pd
from io import BytesIO
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
app.secret_key = '@@268456'  # Change this in production!

USERS_FILE = 'users.json'

# Generate encryption key from secret (store securely in prod)
SECRET_ENCRYPTION_KEY = base64.urlsafe_b64encode(hashlib.sha256(b"268456@@").digest())
fernet = Fernet(SECRET_ENCRYPTION_KEY)

def encrypt_data(data):
    json_data = json.dumps(data).encode()
    return fernet.encrypt(json_data).decode()

def decrypt_data(encrypted_data):
    try:
        decrypted = fernet.decrypt(encrypted_data.encode())
        return json.loads(decrypted)
    except Exception:
        return []

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
    return hash_string(mobile)[:12]  # Short unique ID

def load_transactions(mobile):
    try:
        with open(f'transactions_{mobile}.json', 'r') as f:
            encrypted_data = f.read()
            return decrypt_data(encrypted_data)
    except FileNotFoundError:
        return []

def save_transactions(mobile, transactions):
    encrypted_data = encrypt_data(transactions)
    with open(f'transactions_{mobile}.json', 'w') as f:
        f.write(encrypted_data)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        users = load_users()
        encrypted_mobile = encrypt_mobile(mobile)
        if encrypted_mobile in users and users[encrypted_mobile]['password'] == hash_string(password):
            session['logged_in'] = True
            session['mobile'] = encrypted_mobile
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
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    encrypted_mobile = session.get('mobile')
    users = load_users()
    user = users.get(encrypted_mobile, {})
    transactions = load_transactions(encrypted_mobile)

    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')

    expense_categories = {}
    for t in transactions:
        if t['type'] == 'expense':
            expense_categories[t['description']] = expense_categories.get(t['description'], 0) + t['amount']

    chart_data = {
        'labels': list(expense_categories.keys()),
        'values': list(expense_categories.values())
    }

    return render_template('welcome.html',
                           name=user.get('name'),
                           transactions=transactions,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           chart_data=chart_data)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    encrypted_mobile = session.get('mobile')
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    transaction = {
        'type': request.form['type'],
        'description': request.form['description'],
        'amount': float(request.form['amount']),
        'date': now_ist.strftime('%d %B %Y %I:%M %p') + ' IST'
    }

    transactions = load_transactions(encrypted_mobile)
    transactions.append(transaction)
    save_transactions(encrypted_mobile, transactions)

    return redirect(url_for('welcome'))

@app.route('/cancel_last')
def cancel_last():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    encrypted_mobile = session.get('mobile')
    transactions = load_transactions(encrypted_mobile)

    if transactions:
        transactions.pop()
        save_transactions(encrypted_mobile, transactions)

    return redirect(url_for('welcome'))

@app.route('/reset_all')
def reset_all():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    encrypted_mobile = session.get('mobile')
    save_transactions(encrypted_mobile, [])

    return redirect(url_for('welcome'))

@app.route('/export_excel')
def export_excel():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    encrypted_mobile = session.get('mobile')
    transactions = load_transactions(encrypted_mobile)

    df = pd.DataFrame(transactions)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')

    output.seek(0)
    response = make_response(output.read())
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
