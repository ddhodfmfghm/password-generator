
from flask import Flask, render_template, request
import random
import string

app = Flask(__name__)


def generate_password(length, complexity):
    if complexity == 1:
        chars = string.digits
    elif complexity == 2:
        chars = string.ascii_letters + string.digits
    else:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"

    password = ''.join(random.choice(chars) for i in range(length))
    return password


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