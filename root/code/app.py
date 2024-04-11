from flask import Flask, render_template, request, flash, redirect, url_for, session
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from model import User, Librarian, Section, Book, UserBook, db , BookRequests
from datetime import date
from sqlalchemy.exc import IntegrityError
from flask import send_file

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



@app.route('/user/dashboard', methods=['GET', 'POST'])
# @logged_user_required
def user_dashboard():
    search_keyword = "sample"
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    user_id =  session['user_id']
    user = User.query.filter_by(id=user_id).first()
    firstname_ = user.firstname
    if request.method == 'POST':
        search_keyword = request.form.get('search_keyword')
        section = request.form.get('selected_section')
        print(section, "this is section", search_keyword, "this is search keyword")
        if section != "":
            print("not all section selected")
            section = Section.query.filter_by(section_title=section).first()
            section_id = section.id
            print(section_id, "this is section id")
            books = Book.query.filter(Book.section_id == section_id).all()  
        else:
            print("all section selected")
            books = Book.query.all()
    else:
        books = Book.query.all()
    book_list = []
    section_list = []
    for book in books:
        section = Section.query.get(book.section_id)
        if search_keyword != "sample":
            if search_keyword != None:
                print("search keyword is not none or is available")
                if search_keyword.lower() in book.book_title.lower():
                    book_dict = {
                        'title': book.book_title,
                        'section': section.section_title,
                        'author': book.author,
                        'id': book.id
                        }
                    book_list.append(book_dict)
        else:
            print("search keyword is none or not available")
            book_dict = {
                'title': book.book_title,
                'section': section.section_title,
                'author': book.author,
                'id': book.id
            }
            book_list.append(book_dict)
    #for sections 
    books_section = Book.query.all()
    for book in books_section:
        section = Section.query.get(book.section_id)
        if section.section_title in section_list:
            continue
        section_list.append(section.section_title)
    
    user_data = {"firstname": firstname_, "userid": user_id}
    # print(book_list, "this is book list")
    # Pass the lists to the template
    return render_template('userdash.html', user = user_data ,book_list = book_list, sections = section_list)

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

@app.route('/user/books', methods=['POST', 'GET'])
def user_books():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    user_books_pre = UserBook.query.filter_by(status='accepted').all()
    for user_book in user_books_pre:
        book = Book.query.get(user_book.book_id)
        days_requested = user_book.days_requested
        date_borrowed = user_book.date_borrowed
        if date.today().day - date_borrowed.day > days_requested:
            user_book.status = 'completed'
            user_book.date_returned = date.today()
            db.session.commit()
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
    userbooks_entry  = UserBook(user_id=user_id, book_id=book_id, status='requested', paid = False, days_requested=5)    
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
        user_book.date_returned = date.today()
        db.session.commit()
    return redirect(url_for('user_books'))


@app.route('/user/downloadbook', methods=['GET', 'POST'])
def download_book():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    book_id = request.args.get('book_id')
    user_id = request.args.get('user_id')
    book = Book.query.get(book_id)
    if request.method == 'POST':
        user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id).first()
        user_book.paid = True
        db.session.commit()
        book_link = book.link
        return redirect(book_link)        
    if UserBook.query.filter_by(user_id=user_id, book_id=book_id).first().paid == False:
        flash('Please pay for the book before downloading')
        bookDetails = {
            'book_id': book_id,
            'title': book.book_title,
            'author': book.author,
            'price': '100'
        }
        userDetails = {
            'user_id': user_id,
            'name': User.query.get(user_id).firstname
        }
        
        return render_template('payment.html', bookDetails = bookDetails, userDetails = userDetails)
    else:
        book_link = book.link
        return redirect(book_link)    

@app.route('/user/view_book')
def view_book():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    book_id = request.args.get('book_id')
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('user_dashboard'))
    book_link = book.link
    return render_template('viewbook.html', pdfLink=book_link)    
    


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


@app.route('/library/home', methods=['GET', 'POST'])
def librarian_dashboard():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    lib_id =  session['lib_id']
    librarian = Librarian.query.filter_by(id=lib_id).first()
    libname = librarian.libraryname
    if request.method == 'POST':
        search_keyword = request.form.get('search_keyword')
        sections = Section.query.filter(Section.section_title.ilike(f'%{search_keyword}%')).all()
    else:
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

@app.route('/library/requests', methods=['GET', 'POST'])
def bookrequests():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    book_requests = BookRequests.query.all()
    book_request_list = []
    sections_list = []
    for request_ in book_requests:
        #book title needs to fetched from Book table
        if request.method == 'POST':
            search_keyword = request.form.get('search_keyword')
            selected_section = request.form.get('selected_section')
            print(selected_section, "this is selected section")
            book_title = Book.query.get(request_.book_id).book_title
            if search_keyword.lower() in book_title.lower():
                if selected_section in Section.query.get(Book.query.get(request_.book_id).section_id).section_title:
                    request_dict = {
                        'id': request_.id,
                        'book_title': book_title,
                        'user_id': request_.user_id
                    }
                    book_request_list.append(request_dict)
                    section_name = Section.query.get(Book.query.get(request_.book_id).section_id).section_title
                    sections_list.append(section_name)
        else:
            book_title = Book.query.get(request_.book_id).book_title
            request_dict = {
                'id': request_.id,
                'book_title': book_title,
                'user_id': request_.user_id
            }
            book_request_list.append(request_dict)
            section_name = Section.query.get(Book.query.get(request_.book_id).section_id).section_title
            sections_list.append(section_name)
            

    return render_template('bookrequests.html', book_requests=book_request_list , sections = sections_list)

@app.route('/library/currentbooks', methods=['GET', 'POST'])
def current_books():
    if 'lib_id' not in session: 
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    if request.method == 'POST':
        #here you have to search and filter method and retrun the same as get method    
        search_keyword = request.form.get('search_keyword')
        print(search_keyword, "this is search keyword")
        selected_section = request.form.get('selected_section')
        user_books = UserBook.query.filter_by(status='accepted').all()  
        book_list = []
        sections_ = []
        for user_book in user_books:
            book = Book.query.get(user_book.book_id)
            section = Section.query.get(book.section_id)
            if search_keyword.lower() in book.book_title.lower():
                if selected_section in section.section_title:
                    validity = user_book.days_requested - (date.today().day - user_book.date_borrowed.day)  
                    book_dict = {
                        'title': book.book_title,
                        'author': book.author,
                        'section': section.section_title,
                        'book_id': book.id,
                        'user_id': user_book.user_id,
                        'validity': validity
                    }
                    if section.section_title not in sections_:
                        sections_.append(section.section_title) 
                    book_list.append(book_dict)
        return render_template('libcurrentbooks.html', books=book_list, sections = sections_)
    if request.method == 'GET':
        user_books_pre = UserBook.query.filter_by(status='accepted').all()
        for user_book in user_books_pre:
            book = Book.query.get(user_book.book_id)
            days_requested = user_book.days_requested
            date_borrowed = user_book.date_borrowed
            if date.today().day - date_borrowed.day > days_requested:
                user_book.status = 'completed'
                user_book.date_returned = date.today()
                db.session.commit()
        user_books = UserBook.query.filter_by(status='accepted').all()  
        book_list = []
        sections_ = []
        for user_book in user_books:
            book = Book.query.get(user_book.book_id)
            section = Section.query.get(book.section_id)
            validity = user_book.days_requested - (date.today().day - user_book.date_borrowed.day)  

            book_dict = {
                'title': book.book_title,
                'author': book.author,
                'section': section.section_title,
                'book_id': book.id,
                'user_id': user_book.user_id,
                'validity': validity
            }
            if section.section_title not in sections_:
                sections_.append(section.section_title) 
            book_list.append(book_dict)
        print(book_list, "this is book list")
        return render_template('libcurrentbooks.html', books=book_list, sections = sections_)    


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
        link = request.form.get('link')
        book_image = request.form.get('bookImage')
        new_book = Book(section_id=section_id, book_title=book_title, author=author, content=content, date_created=date.today(), Image=book_image, link = link)
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
        user_book.date_borrowed = date.today()
        user_book.days_requested = book_request.days_requested
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

@app.route('/library/revoke', methods=['POST'])
def revoke_access():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    print("revoking access 1st step")
    user_id = request.form.get('user_id')
    book_id = request.form.get('book_id')
    print(user_id, book_id, "this is user id and book id for revoke access")
    # user_book = 
    print("book id" , book_id , "done")
    print(type(book_id))
    user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id).first()
    print(user_book, "this is user book")
    if user_book:
        user_book.status = 'completed'
        print("inside user book existsrevoked access")
        user_book.date_returned = date.today()
        db.session.commit()
    return redirect(url_for('current_books'))

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