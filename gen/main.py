import random
import string, os
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = '123'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.txt')
PASSWORDS_FILE = os.path.join(BASE_DIR, 'passwords.txt')


def generate_password(length, complexity):
    if complexity == 1:
        chars = string.digits
    elif complexity == 2:
        chars = string.ascii_letters + string.digits
    else:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"

    password = ''.join(random.choice(chars) for i in range(length))
    return password


def load_users():
    users = []
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    username, password, role = line.strip().split('|')
                    users.append({
                        'username': username,
                        'password': password,
                        'role': role
                    })
    except FileNotFoundError:
        default_users = [
            {'username': 'admin', 'password': 'admin', 'role': 'admin'},
            {'username': 'user', 'password': 'user', 'role': 'user'}
        ]
        save_users(default_users)
        users = default_users
    return users


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        for user in users:
            f.write(f"{user['username']}|{user['password']}|{user['role']}\n")


def user_exists(username):
    users = load_users()
    for user in users:
        if user['username'] == username:
            return True
    return False


def add_user(username, password, role='user'):
    users = load_users()
    users.append({
        'username': username,
        'password': password,
        'role': role
    })
    save_users(users)


def save_user_password(username, login1, website, password):
    with open(PASSWORDS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{username}|{login1}|{website}|{password}\n")


def load_user_passwords(username):
    passwords = []
    try:
        with open(PASSWORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    user, login1, website, pwd = line.strip().split('|')
                    if user == username:
                        passwords.append({
                            'login1': login1,
                            'website': website,
                            'password': pwd
                        })
    except FileNotFoundError:
        pass
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

        users = load_users()
        user_found = False
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')
                print(session)
                user_found = True
                return redirect(url_for('index'))

        if not user_found:
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
            # Регистрируем нового пользователя
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

    save_user_password(session['username'],login1, website, password)
    return redirect(url_for('index'))


@app.route('/my_passwords')
@login_required
def my_passwords():
    passwords = load_user_passwords(session['username'])
    return render_template('passwords.html', passwords=passwords)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)