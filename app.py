from flask import Flask, render_template
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return render_template('login.html')


from routes.register import *


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)