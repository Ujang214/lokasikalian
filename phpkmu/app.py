from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os
import pymysql
import datetime
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

logging.basicConfig(level=logging.INFO)

connection = pymysql.connect(
    host='localhost',
    user=db_username,
    password=db_password,
    db=db_name,
    cursorclass=pymysql.cursors.DictCursor
)

def authenticate(username, password):
    with connection.cursor() as cursor:
        sql = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(sql, (username, password))
        result = cursor.fetchone()
        return result is not None

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    with connection.cursor() as cursor:
        sql_get_users = "SELECT username FROM users"
        cursor.execute(sql_get_users)
        users = [user['username'] for user in cursor.fetchall()]

    return render_template('login.html', users=users)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if authenticate(username, password):
        session['username'] = username

        # Catat informasi login
        with connection.cursor() as cursor:
            sql_insert_login = "INSERT INTO user_logins (username, timestamp) VALUES (%s, %s)"
            cursor.execute(sql_insert_login, (username, datetime.datetime.now()))
            connection.commit()

        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='Invalid credentials')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    if 'username' in session:
        username = session.pop('username')

        # Catat informasi logout
        with connection.cursor() as cursor:
            sql_insert_logout = "INSERT INTO user_logouts (username, timestamp) VALUES (%s, %s)"
            cursor.execute(sql_insert_logout, (username, datetime.datetime.now()))
            connection.commit()

    return redirect(url_for('home'))

@app.route('/admin-panel')
def admin_panel():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('home'))

    with connection.cursor() as cursor:
        # Ambil informasi pengguna yang sedang login
        sql_get_logins = "SELECT * FROM user_logins"
        cursor.execute(sql_get_logins)
        user_logins = cursor.fetchall()

        # Ambil informasi sesi logout
        sql_get_logouts = "SELECT * FROM user_logouts"
        cursor.execute(sql_get_logouts)
        user_logouts = cursor.fetchall()

    return render_template('admin_panel.html', user_logins=user_logins, user_logouts=user_logouts)

if __name__ == '__main__':
    app.run(debug=False)