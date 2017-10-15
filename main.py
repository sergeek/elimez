import os
import hashlib
from flask import Flask, request, redirect, render_template, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy 
import cgi


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://elimez:unitfour@localhost:8889/elimez'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = 'MakeAWish'

#Create User, List, and Task DBs
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    lists = db.relationship('List', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship('Task', backref='owner')

    def __init__(self, title, owner):
        self.title = title
        self.owner = owner

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(120))
    completed = db.Column(db.Boolean)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))

    def __init__(self, item, owner):
        self.item = item
        self.completed = False
        self.list_id = owner

#Handle user registration
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

            return redirect('/lists')
        else: 
            flash('User already exist', 'error')
            return render_template('register.html')
    
    return render_template('register.html', page_title="Register")

#Verify user login data, and store username in session
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(str.encode(password)).hexdigest()
        user = User.query.filter_by(username=username).first()
        if user and (password_hash == user.password):
            session['username'] = username
            return redirect("/lists")
        else:
            flash('User password incorrect, or user does not exist', 'error')

            return render_template("login.html", page_title = "Login")

    return render_template('login.html', page_title="Login")

#Delete username session on logout
@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

#Create new list handler: first displays a title form page, and then to-do list on next btn
@app.route("/title", methods=['POST', 'GET'])
def title():
    if request.method == 'POST':
        title = request.form['title']
        if title == '':
            flash("Title can't be empty", 'error')
            return redirect('/title')

        owner = User.query.filter_by(username=session['username']).first()
        new_list = List(title, owner)
        db.session.add(new_list)
        db.session.commit()

        session['title'] = title
        return render_template('todos.html', page_title=title, list_id=new_list.id)

    return render_template('title.html', page_title="Create List")

#Adding tasks on a newly created list only
@app.route("/add-task", methods=['POST'])
def add_task():
    title = session['title']
    task_item = request.form['task']
    task_owner = request.form['list-id']
    new_task = Task(task_item, task_owner)
    db.session.add(new_task)
    db.session.commit()
    tasks = Task.query.filter_by(list_id=task_owner).all()
    
    return render_template('todos.html', page_title=title, tasks=tasks, list_id=task_owner)

#Displaying all the list for the given user
@app.route('/lists')
def my_lists():
    logged_user = User.query.filter_by(username=session['username']).first()
    lists = List.query.filter_by(owner_id=logged_user.id).all()

    return render_template('lists.html', page_title='My Lists', lists=lists)

#Displaying todos page for the list title clicked
@app.route('/display')
def show_list():
    list_id=request.args.get('list_id')
    tasks = Task.query.filter_by(list_id=list_id).all()

    return render_template('todos.html', page_title=title, tasks=tasks, list_id=list_id)


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html', page_title="Elimez")

if __name__ == '__main__':
    app.run()