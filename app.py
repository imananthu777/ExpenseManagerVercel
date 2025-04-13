import streamlit as st
import hashlib
import json
import os
from datetime import datetime

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
    return hash_string(mobile)[:12]

def load_transactions(mobile):
    try:
        with open(f'transactions_{mobile}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_transactions(mobile, transactions):
    with open(f'transactions_{mobile}.json', 'w') as f:
        json.dump(transactions, f)

def login():
    st.title("Login")

    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type='password')
    login_btn = st.button("Login")

    if login_btn:
        users = load_users()
        encrypted_mobile = encrypt_mobile(mobile)
        if encrypted_mobile in users and users[encrypted_mobile]['password'] == hash_string(password):
            st.session_state.logged_in = True
            st.session_state.mobile = encrypted_mobile
            st.session_state.name = users[encrypted_mobile]['name']
            st.experimental_rerun()
        else:
            st.error("Invalid mobile number or password.")

def register():
    st.title("Register")

    name = st.text_input("Name")
    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type='password')
    email = st.text_input("Email (optional)")
    register_btn = st.button("Register")

    if register_btn:
        users = load_users()
        encrypted_mobile = encrypt_mobile(mobile)
        if encrypted_mobile in users:
            st.error("Mobile number already registered!")
        else:
            users[encrypted_mobile] = {
                'password': hash_string(password),
                'name': name,
                'email': email
            }
            save_users(users)
            st.success("Registration successful! You can now log in.")

def dashboard():
    st.title(f"Welcome, {st.session_state.name} 👋")

    mobile = st.session_state.mobile
    transactions = load_transactions(mobile)

    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')

    st.metric("Total Income", f"₹{total_income}")
    st.metric("Total Expenses", f"₹{total_expenses}")

    st.subheader("Add New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        t_type = st.selectbox("Type", ["income", "expense"])
    with col2:
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")
    description = st.text_input("Description")

    if st.button("Add Transaction"):
        new_transaction = {
            'type': t_type,
            'description': description,
            'amount': amount,
            'date': datetime.now().strftime('%d %B %Y %I:%M %p') + ' IST'
        }
        transactions.append(new_transaction)
        save_transactions(mobile, transactions)
        st.success("Transaction added.")
        st.experimental_rerun()

    if transactions:
        st.subheader("Transaction History")
        st.table(transactions[::-1])  # Show newest first

        if st.button("Cancel Last Transaction"):
            transactions.pop()
            save_transactions(mobile, transactions)
            st.success("Last transaction removed.")
            st.experimental_rerun()

    st.button("Logout", on_click=lambda: logout())

def logout():
    st.session_state.clear()
    st.experimental_rerun()

# App Navigation
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

menu = st.sidebar.selectbox("Menu", ["Login", "Register"] if not st.session_state.logged_in else ["Dashboard", "Logout"])

if not st.session_state.logged_in:
    if menu == "Login":
        login()
    elif menu == "Register":
        register()
else:
    if menu == "Dashboard":
        dashboard()
    elif menu == "Logout":
        logout()
