import random
import string
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = '123'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.db')


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')

    # Создаем таблицу паролей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            login1 TEXT,
            website TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Добавляем стандартных пользователей если их нет
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('admin', 'admin', 'admin'))
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('user', 'user', 'user'))

    conn.commit()
    conn.close()


def generate_password(length, complexity):
    if complexity == 1:
        chars = string.digits
    elif complexity == 2:
        chars = string.ascii_letters + string.digits
    else:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"

    password = ''.join(random.choice(chars) for i in range(length))
    return password


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def user_exists(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user is not None


def add_user(username, password, role='user'):
    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                 (username, password, role))
    conn.commit()
    conn.close()


def save_user_password(username, login1, website, password):
    conn = get_db_connection()
    conn.execute('INSERT INTO passwords (username, login1, website, password) VALUES (?, ?, ?, ?)',
                 (username, login1, website, password))
    conn.commit()
    conn.close()


def load_user_passwords(username):
    conn = get_db_connection()
    passwords = conn.execute(
        'SELECT * FROM passwords WHERE username = ?', (username,)
    ).fetchall()
    conn.close()
    return passwords


# Декоратор для проверки аутентификации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not password:
            flash('Заполните все поля', 'error')
        elif len(username) < 3:
            flash('Имя пользователя должно быть не менее 3 символов', 'error')
        elif len(password) < 4:
            flash('Пароль должен быть не менее 4 символов', 'error')
        elif password != confirm_password:
            flash('Пароли не совпадают', 'error')
        elif user_exists(username):
            flash('Пользователь с таким именем уже существует', 'error')
        else:
            add_user(username, password)
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    password = None

    if request.method == 'POST':
        length = int(request.form['length'])
        complexity = int(request.form['complexity'])
        password = generate_password(length, complexity)

    return render_template('index.html', password=password)


@app.route('/save_password', methods=['POST'])
@login_required
def save_password():
    login1 = request.form['login1']
    website = request.form['website']
    password = request.form['password']

    if not website:
        flash('Введите название сайта', 'error')
        return redirect(url_for('index'))

    save_user_password(session['username'], login1, website, password)
    return redirect(url_for('index'))


@app.route('/my_passwords')
@login_required
def my_passwords():
    passwords = load_user_passwords(session['username'])
    return render_template('passwords.html', passwords=passwords)


if __name__ == '__main__':
    init_db()  # Инициализируем базу данных при запуске
    app.run(debug=True, host='0.0.0.0', port=5000)