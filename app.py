from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(16)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return login_process()
    return render_template('login.html')

def login_process():

    username = request.form['username']
    password = request.form['password']
    user = mongo.db.users.find_one({"username": username})

    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        print(request.form)
        username = request.form['username']
        password = request.form['password']
        user_exists = mongo.db.users.find_one({"username": username})
        if user_exists:
            flash('Username already exists.')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({
            "username": username,
            "password": hashed_password
        })
        flash('User created successfully. Please login.')
        return redirect(url_for('login'))
    return render_template('signup_new.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/addperson', methods=['GET', 'POST'])
def addperson():
    return render_template('addPerson.html')

@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    return render_template('contact_us_new.html')

@app.route('/people', methods=['GET', 'POST'])
def people():
    return render_template('people.html')

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    return render_template('stats.html')

@app.route('/update_expense', methods=['GET', 'POST'])
def update_expense():
    return render_template('update_expense.html')

if __name__ == '__main__':
    # app.secret_key = 'your_secret_key_here'
    app.run(debug=True)
