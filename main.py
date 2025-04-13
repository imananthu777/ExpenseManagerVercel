from flask import Flask, render_template, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key!

# Mock database
users_db = {}

def send_otp(phone_number):
    otp = random.randint(100000, 999999)
    users_db[phone_number] = otp  # Store OTP in the mock database
    print(f'Sending OTP {otp} to {phone_number}')  # Simulate sending OTP

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        send_otp(phone_number)
        session['phone_number'] = phone_number  # Store phone number in session
        return redirect(url_for('verify_otp'))

    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        phone_number = session.get('phone_number')
        otp = request.form['otp']

        if phone_number in users_db and users_db[phone_number] == int(otp):
            session['logged_in'] = True
            return redirect(url_for('welcome'))

        return "OTP Verification Failed. Please try again."

    return render_template('verify.html')

@app.route('/welcome')
def welcome():
    if session.get('logged_in'):
        return "Welcome! You are logged in."
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)