import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash



app = Flask(__name__)
app.secret_key = 'your-secret-key-123'

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
    return  [
            {'username': 'admin', 'password': 'admin', 'role': 'admin'},
            {'username': 'user', 'password': 'user', 'role': 'user'}
        ]




# Декоратор для проверки аутентификации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Маршруты аутентификации
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
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))

        if not user_found:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


# Защищенные маршруты
@app.route('/')
@login_required
def index1():
    return render_template('index.html', username=session.get('username'))
    print(session)


@app.route('/', methods=['GET', 'POST'])
def index():
    password = None

    if request.method == 'POST':
        length = int(request.form['length'])
        complexity = int(request.form['complexity'])
        password = generate_password(length, complexity)

    return render_template('index.html', password=password)



if __name__ == '__main__':
    app.run(debug=True)
