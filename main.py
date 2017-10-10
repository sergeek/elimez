from flask import Flask, request, redirect, render_template, url_for, flash, session

from flask_sqlalchemy import SQLAlchemy 
import hashlib
import os

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://elimez:unitfour@localhost:8889/elimez'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = 'MakeAWish'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(str.encode(password)).hexdigest()
        verify = request.form['verify']

        if len(username) < 4:
            flash('Username must be at least 4 characters', 'error')
            return render_template('register.html', username=username)
        if len(password) < 4:
            flash('Password must be at least 4 characters', 'error')
            return render_template('register.html', username=username)
        if password != verify:
            flash('Passwords do not match', 'error')
            return render_template('register.html', username=username)

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password_hash)
            db.session.add(new_user)
            db.session.commit()

            session['username'] = username

            return redirect('/')
        else: 
            flash('User already exist', 'error')
            return render_template('register.html')
    
    return render_template('register.html', page_title="Register")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(str.encode(password)).hexdigest()
        user = User.query.filter_by(username=username).first()
        if user and password_hash:
            session['username'] = username
            return redirect("/")
        else:
            flash('User password incorrect, or user does not exist', 'error')

            return render_template("login.html", page_title = "Login")

    return render_template('login.html', page_title="Login")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html', page_title="Elimez")

if __name__ == '__main__':
    app.run()