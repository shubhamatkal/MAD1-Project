from flask import Flask, render_template, request, flash, redirect, url_for, session
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from model import User, Librarian, Section, Book, UserBook, db

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')



db.init_app(app)

with app.app_context():
    db.create_all()



#defining the wrappers for auth, admin and user
def logged_library_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'lib_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('librarian_login'))
        user = User.query.get(session['lib_id'])
    return inner

def logged_user_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('user_login'))
    return inner


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user/login')
def user_login():
    return render_template('userlogin.html')

@app.route('/user/login', methods=['POST'])
def user_login_post():
    username = request.form.get('u_name')
    password = request.form.get('pwd')
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('Username does not exist')
        return redirect(url_for('user_login'))
    
    if not check_password_hash(user.passhashed, password):
        flash('Incorrect password')
        return redirect(url_for('user_login'))
    
    session['user_id'] = user.id
    flash('Login successful')
    return redirect(url_for('user_dashboard'))


@app.route('/user/register')
def user_register():
    return render_template('register.html')

@app.route('/user/register', methods=['POST'])
def user_register_post():
    username = request.form.get('u_name')
    firstname = request.form.get('first_name')
    lastname = request.form.get('last_name')
    password = request.form.get('password')
    confirm_password = request.form.get('c_password')
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('user_register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('user_register'))
    
    password_hash = generate_password_hash(password)
    
    new_user = User(username=username, passhashed=password_hash, firstname=firstname, lastname=lastname)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('user_login'))

@app.route('/user/dashboard', methods=['POST', 'GET'])
@logged_user_required
def user_dashboard():
    if request.method == 'POST':
        return "Not defined yet"
    elif request.method == 'GET':
        user_id =  session['user_id']
        user = User.query.filter_by(id=user_id).first()
        firstname_ = user.firstname
        user_data = {"firstname": firstname_}
        return render_template('userdash.html', user=user_data)

@app.route('/user/books', methods=['POST', 'GET'])
@logged_user_required
def user_books():
    user_data = {"username": 'Shubham Atkal'}
    return render_template('userbooks.html', user=user_data)

@app.route('/library/login')
def librarian_login():
    return render_template('liblogin.html')

@app.route('/library/login', methods=['POST'])
def librarian_login_post():
    username = request.form.get('u_name')
    password = request.form.get('pwd')
    
    library = Librarian.query.filter_by(username=username).first()
    
    if not library:
        flash('Username does not exist')
        return redirect(url_for('librarian_login'))
    
    if not check_password_hash(library.passhashed, password):
        flash('Incorrect password')
        return redirect(url_for('librarian_login'))
    
    session['lib_id'] = library.id
    flash('Login successful')
    return redirect(url_for('librarian_dashboard'))

@app.route('/library/register')
def librarian_register():
    return render_template('registerlib.html')

@app.route('/library/register', methods=['POST'])
def librarian_register_post():
    username = request.form.get('u_name')
    libraryname = request.form.get('libraryname')
    password = request.form.get('pwd')
    confirm_password = request.form.get('c_pwd')
    #username, passhashed, firstname, lastname
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('librarian_register'))
    
    library = Librarian.query.filter_by(username=username).first()
    if library:
        flash('Username already exists')
        return redirect(url_for('librarian_register'))
    
    password_hash = generate_password_hash(password)
    
    new_user = Librarian(username=username, passhashed=password_hash, libraryname=libraryname)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('librarian_register'))


@app.route('/library/home')
@logged_library_required
def librarian_dashboard():
    return render_template('libdash.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/user/logout')
@logged_user_required
def user_logout():
    session.pop('user_id')
    return redirect(url_for('user_login'))

@app.route('/library/logout')
@logged_library_required
def lib_logout():
    session.pop('lib_id')
    return redirect(url_for('librarian_login'))

if __name__ == '__main__':
    app.run(debug=True, port=3000)