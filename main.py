
from flask import Flask, render_template, request, redirect, url_for, session
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key!

# Mock database
users_db = {}  # Format: {mobile: {'password': hashed_password, 'name': name, 'email': email}}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        
        if mobile in users_db and users_db[mobile]['password'] == hash_password(password):
            session['logged_in'] = True
            session['mobile'] = mobile
            return redirect(url_for('welcome'))
        
        return "Invalid mobile number or password. Please try again."

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']
        email = request.form.get('email', '')  # Optional email
        
        if mobile in users_db:
            return "Mobile number already registered!"
        
        users_db[mobile] = {
            'password': hash_password(password),
            'name': name,
            'email': email
        }
        return redirect(url_for('home'))
        
    return render_template('register.html')

@app.route('/welcome')
def welcome():
    if session.get('logged_in'):
        mobile = session.get('mobile')
        user = users_db.get(mobile, {})
        return f"Welcome {user.get('name')}! You are logged in."
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
