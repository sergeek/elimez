import os
import hashlib
from flask import Flask, request, redirect, render_template, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy 
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://elimez:unitfour@localhost:8889/elimez')
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'MakeAWish'

#Create many to many relationship between List and a User
users_lists = db.Table('users_lists',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('list_id', db.Integer, db.ForeignKey('list.id'))
    )

#Create User, List, and Task DBs
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    lists = db.relationship('List', secondary=users_lists, 
    backref=db.backref('admins', lazy = 'dynamic'))

    def __init__(self, username, password):
        self.username = username
        self.password = password

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    items = db.relationship('Task', backref='owner')

    def __init__(self, title):
        self.title = title

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(120))
    completed = db.Column(db.Boolean)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))

    def __init__(self, item, owner):
        self.item = item
        self.completed = False
        self.list_id = owner

@app.before_request
def require_login():
    allowed_routes = ['register', 'login', 'index', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

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
    username=session['username']
    if request.method == 'POST':
        title = request.form['title']
        if title == '':
            flash("Title can't be empty", 'error')
            return redirect('/title')

        owner = User.query.filter_by(username=session['username']).first()
        new_list = List(title)
        db.session.add(new_list)
        db.session.commit()
        new_list.admins.append(owner)
        db.session.commit()
        task_owner = new_list.id

        return redirect("/display?list_id={0}".format(task_owner))
        
    return render_template('title.html', page_title="Create List", username=username)

#Adding tasks on a newly created list only
@app.route("/add-task", methods=['POST'])
def add_task():
    task_item = request.form['task']
    task_owner = request.form['list-id']
    list_obj = List.query.filter_by(id=task_owner).first()

    if task_item == "":
        flash("Your task is empty", "error")
        return redirect("/display?list_id={0}".format(task_owner))
    new_task = Task(task_item, task_owner)
    db.session.add(new_task)
    db.session.commit()

    return redirect("/display?list_id={0}".format(task_owner))
    
#Add user the the list handler
@app.route("/add-user", methods=['POST'])
def add_user():
    task_owner = request.form['list-id']
    list_obj = List.query.filter_by(id=task_owner).first()
    get_username = request.form['user']
    user = User.query.filter_by(username=get_username).first()

    if user and user not in list_obj.admins:
        list_obj.admins.append(user)
        db.session.commit()
        return redirect("/display?list_id={0}".format(task_owner))
    else:
        if user in list_obj.admins:
            flash('User already added', 'error')
        else:
            flash('User does not exist', 'error')
        return redirect("/display?list_id={0}".format(task_owner))

#Displaying all the list for the given user
@app.route('/lists')
def my_lists():
    logged_user = User.query.filter_by(username=session['username']).first()
    lists = logged_user.lists
    username = logged_user.username

    return render_template('lists.html', page_title='My Lists', lists=lists, username=username)

#Displaying todos page for the list title clicked
@app.route('/display')
def show_list():
    logged_user = User.query.filter_by(username=session['username']).first()
    list_id=request.args.get('list_id')
    list_obj = List.query.filter_by(id=list_id).first()

    #Security check part a: find all lists that belong to user
    my_lists = logged_user.lists
    my_list_ids = []
    for lst in my_lists:
        my_list_ids.append(lst.id)

    #Security check part b: make sure user has permission to the list
    if list_obj.id in my_list_ids:
        tasks = Task.query.filter_by(list_id=list_id).all()
        title = list_obj.title
        username=session['username']
        admins = list_obj.admins
        return render_template('todos.html', page_title=title, tasks=tasks, list_id=list_id, username=username, admins=admins)
    else: 
        return "Something went wrong"

#Toggle the switch to completed/not-completed
@app.route('/complete-task', methods=['POST'])
def complete():

    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)

    if task.completed == False:
        task.completed = True
    else: task.completed = False
    db.session.add(task)
    db.session.commit()
    task_owner = task.list_id

    return redirect("/display?list_id={0}".format(task_owner))
   
@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html', page_title="Elimez")

if __name__ == '__main__':
    app.run()