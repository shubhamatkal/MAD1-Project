from flask import Flask, render_template, request, flash, redirect, url_for, session
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from model import User, Librarian, Section, Book, UserBook, db , BookRequests
from datetime import date
from sqlalchemy.exc import IntegrityError

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



@app.route('/user/dashboard')
# @logged_user_required
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    user_id =  session['user_id']
    user = User.query.filter_by(id=user_id).first()
    firstname_ = user.firstname
    books = Book.query.all()
    book_list = []
    for book in books:
        section = Section.query.get(book.section_id)
        if section:
            book_dict = {
            'title': book.book_title,
            'section': section.section_title,
            'author': book.author,
            'id': book.id
            }
            book_list.append(book_dict)
        book_list.append(book_dict)
    user_data = {"firstname": firstname_, "userid": user_id}

    # Pass the lists to the template
    return render_template('userdash.html', user = user_data ,book_list = book_list)

@app.route('/user/cancelbook')
def cancel_book():
    book_id = request.args.get('book_id')
    user_id = request.args.get('user_id')
    # print(book_id, user_id, "this is book id and user id")
    user_book = UserBook.query.filter_by(book_id=book_id, user_id=user_id, status='requested').first()
    user_request = BookRequests.query.filter_by(book_id=book_id, user_id=user_id).first()
    if user_book:
        db.session.delete(user_book)
        db.session.delete(user_request)
        db.session.commit()
        # print("deleted book")
    return redirect(url_for('user_books'))

@app.route('/user/dashboard', methods=['POST'])
def user_dashboard_post():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    return "Not defined yet"

@app.route('/user/books', methods=['POST', 'GET'])
def user_books():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    user_id = session['user_id']
    user = User.query.filter_by(id=user_id).first()
    firstname_ = user.firstname

    
    # Fetching requested books
    requested_books = []
    book_requests = UserBook.query.filter_by(user_id=user_id, status='requested').all()
    
    for request in book_requests:
        book = Book.query.get(request.book_id)
        section_ = Section.query.get(book.section_id)
        if book:
            book_dict = {
                'title': book.book_title,
                'section': section_,
                'author': book.author,
                'id': book.id
            }
            requested_books.append(book_dict)

    # Fetching current books
    current_books = []
    user_books = UserBook.query.filter_by(user_id=user_id, status='accepted').all()
    for user_book in user_books:
        book = Book.query.get(user_book.book_id)
        section_ = Section.query.get(book.section_id)
        if book:
            book_dict = {
                'title': book.book_title,
                'section': section_.section_title,
                'author': book.author,
                'id': book.id
            }
            current_books.append(book_dict)

    # Fetching completed books
    completed_books = []
    user_books = UserBook.query.filter_by(user_id=user_id, status='completed').all()
    for user_book in user_books:
        book = Book.query.get(user_book.book_id)
        section_ = Section.query.get(book.section_id)
        if book:
            book_dict = {
                'title': book.book_title,
                'section': section_.section_title,
                'author': book.author,
                'id': book.id
            }
            completed_books.append(book_dict)
    print(completed_books, "this is completed books")
    user_data = {"firstname": firstname_, "userid": user_id}
    return render_template('userbooks.html', user=user_data, requestedbooks=requested_books, currentbooks=current_books, completedbooks=completed_books )

@app.route('/user/requestbook', methods=['GET'])
def request_book():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    
    user_id = session['user_id']
    book_id = request.args.get('book_id')
    book = Book.query.get(book_id)
    if book:
        pass
        # Rest of the code
    else:
        flash('Book not found')
        return redirect(url_for('user_dashboard'))
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('user_dashboard'))
    # Add the request to BookRequests database
    userbooks_entry  = UserBook(user_id=user_id, book_id=book_id, status='requested')
    new_request = BookRequests(book_id= book_id, user_id=user_id, date = date.today() ,days_requested=5)
    db.session.add(new_request)
    db.session.add(userbooks_entry)
    db.session.commit()
    
    flash('Book request submitted successfully')
    return redirect(url_for('user_books'))

@app.route('/user/return_book/<int:book_id>/<int:user_id>')
def return_book(book_id, user_id):
    user_book = UserBook.query.filter_by(book_id=book_id, user_id=user_id).first()
    if user_book:
        user_book.status = 'completed'
        db.session.commit()
    return redirect(url_for('user_books'))


#library routes

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
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        flash('You cannot register a library again. Please login using your credentials.')
        return redirect(url_for('librarian_login'))
    return redirect(url_for('librarian_login'))


@app.route('/library/home')
def librarian_dashboard():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    lib_id =  session['lib_id']
    librarian = Librarian.query.filter_by(id=lib_id).first()
    libname = librarian.libraryname
    sections = Section.query.all()
    section_list = []
    for section in sections:
        section_dict = {
            'name': section.section_title,
            'datecreated': section.date_created,
            'description': section.description,
            'id': section.id
        }
        section_list.append(section_dict)
    return render_template('libdash.html', libinfo={"Name": libname}, sections=section_list)    

@app.route('/library/requests', methods=['GET'])
def bookrequests():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    book_requests = BookRequests.query.all()
    book_request_list = []
    for request in book_requests:
        #book title needs to fetched from Book table
        book_title = Book.query.get(request.book_id).book_title
        request_dict = {
            'id': request.id,
            'book_title': book_title,
            'user_id': request.user_id
        }
        book_request_list.append(request_dict)

    return render_template('bookrequests.html', book_requests=book_request_list)


@app.route('/library/addsection', methods=['GET', 'POST'])
def add_section():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    
    if request.method == 'GET':
        return render_template('addsection.html')
    if request.method == 'POST':
        section_title = request.form.get('sectionName')
        description = request.form.get('sectionDescription')
        section_image = request.form.get('sectionImage')

        new_section = Section(section_title=section_title, date_created=date.today(), description=description, Image=section_image)
        db.session.add(new_section)
        db.session.commit()
        return redirect(url_for('librarian_dashboard'))

@app.route('/library/addbook', methods=['GET', 'POST'])
def add_book():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    if request.method == 'GET':
        section_id = request.args.get('section_id')
        return render_template('addbook.html', )
    if request.method == 'POST':
        section_id = request.args.get('section_id')
        book_title = request.form.get('bookTitle')
        author = request.form.get('author')
        content = request.form.get('content')
        book_image = request.form.get('bookImage')
        new_book = Book(section_id=section_id, book_title=book_title, author=author, content=content, date_created=date.today(), Image=book_image)
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('librarian_dashboard'))

@app.route('/library/showbooks', methods=['GET', 'POST'])
def show_books():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    if request.method == 'POST':
        section_id = request.form.get('section_id')
        search_keyword = request.form.get('search_keyword')
        books = Book.query.filter(Book.section_id == section_id, Book.book_title.ilike(f'%{search_keyword}%')).all()
    else:
        section_id = request.args.get('section_id')
        books = Book.query.filter(Book.section_id == section_id).all()
    book_list = []
    for book in books:
        book_dict = {
            'title': book.book_title,
            'author': book.author,
            'content': book.content,
            'image': book.Image
        }
        book_list.append(book_dict)
    return render_template('showbooks.html', section_id=section_id, books=book_list)

@app.route('/library/view_book_details')
def view_details():
    print("now in view details function")
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    r_id = request.args.get('r_id')
    print(r_id, "this is r_id for view books")
    book_request = BookRequests.query.get(r_id)
    if book_request:
        author = Book.query.get(book_request.book_id).author
        book_title = Book.query.get(book_request.book_id).book_title
        book_request_info = {
            'id': book_request.id,
            'book_title': book_title,
            'author': author,
            'user_id': book_request.user_id
        }
        print(book_request_info, "this is book request info")
        return render_template('viewdetails.html', request_info=book_request_info)
    else:
        flash('Invalid request ID')
        return redirect(url_for('bookrequests'))

@app.route('/library/grantboooks')
def grantboooks():
    r_id = request.args.get('r_id')
    print(r_id, "this is r_id for grant books")
    book_request = BookRequests.query.get(r_id)  # renamed 'request' to 'book_request'
    if book_request:
        book_id = book_request.book_id
        user_id = book_request.user_id
    user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id).first()
    if user_book:
        user_book.status = 'accepted'
        db.session.delete(book_request)
        db.session.commit()
    else:
        flash('UserBook tuple not found')
    return redirect(url_for('bookrequests'))

@app.route('/library/rejectbooks')
def rejectbooks():
    # Code to handle reject books functionality
    r_id = request.args.get('r_id')
    book_request = BookRequests.query.get(r_id)
    if book_request:
        book_id = book_request.book_id
        user_id = book_request.user_id
    user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id).first()
    if user_book:
        db.session.delete(user_book)
        db.session.delete(book_request)
        db.session.commit()
    else:
        flash('UserBook tuple not found')

    return redirect(url_for('bookrequests'))


@app.route('/view_book/<int:book_id>')
def view_book(book_id):
    if 'user_id' not in session and 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        if session.get('user_id'):
            return redirect(url_for('user_dashboard'))
        else:
            return redirect(url_for('librarian_dashboard'))    
    book_link = book.link
    return render_template('view_book.html', book_link=book_link)

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/user/logout')
def user_logout():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    session.pop('user_id')
    return redirect(url_for('user_login'))

@app.route('/library/logout')
def lib_logout():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    session.pop('lib_id')
    return redirect(url_for('librarian_login'))

if __name__ == '__main__':
    app.run(debug=True, port=3000)