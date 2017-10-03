from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route('/register', methods=['POST', 'GET'])
def register():
    return render_template('register.html', page_title="Register")

@app.route('/login', methods=['POST', 'GET'])
def login():
    return render_template('login.html', page_title="Login")

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html', page_title="Elimez")

if __name__ == '__main__':
    app.run()