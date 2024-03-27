from flask import Flask, render_template, request, flash, redirect, url_for, session
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

import os

app = Flask(__name__)


from databasee import User, Librarian, Section, Book, UserBook

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user/login')
def login():
    return render_template('login.html')

@app.route('/user/login', methods=['POST'])
def login_post():
    username = request.form.get('u_name')
    password = request.form.get('pwd')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('user/login'))
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('Username does not exist')
        return redirect(url_for('user/login'))
    
    if not check_password_hash(user.passhash, password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    flash('Login successful')
    return redirect(url_for('userdashboard'))



@app.route('user/register')
def register():
    return render_template('register.html')

@app.route('user/register', methods=['POST'])
def register_post():
    username = request.form.get('u_name')
    firstname = request.form.get('first_name')
    lastname = request.form.get('last_name')
    password = request.form.get('password')
    confirm_password = request.form.get('c_password')

    if not username or not password or not confirm_password or not firstname:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    
    new_user = User(username=username, passhash=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))


@app.route('/userdashboard', methods=['POST', 'GET'])
def user_dashboard():
    user_data = {"username": 'Shubham Atkal'}
    if request.method == 'POST':
        return render_template('userdash.html', user=user_data)
    elif request.method == 'GET':
        # Handle the POST request here
        # Add your code to process the form data
        return render_template('userdash.html', user=user_data)

@app.route('/user/books', methods=['POST', 'GET'])
def user_books():
    user_data = {"username": 'Shubham Atkal'}
    return render_template('userbooks.html', user=user_data)

@app.route('/library/login')
def librarian_login():
    return render_template('liblogin.html')

@app.route('/library/register')
def librarian_register():
    return render_template('registerlib.html')

@app.route('/library/home', methods=['POST'])
def librarian_dashboard():
    return render_template('libdash.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

if __name__ == '__main__':
    app.run(debug=True, port=3000)