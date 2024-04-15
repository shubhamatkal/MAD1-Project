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

@app.route('/about')
def about():
    return render_template('about.html')

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
        book_id = book.id
        avg_rating = UserBook.query.filter_by(book_id=book_id, status = 'completed').all()
        if avg_rating:
            avg_rating_ = 0
            n = 0
            for rating in avg_rating:
                if rating.rating != "":
                    avg_rating_ += int(rating.rating)
                    n += 1
            if n != 0:
                avg_rating = avg_rating_/n
            else:
                avg_rating = "Error"
        else:
            avg_rating = "-"
        section = Section.query.get(book.section_id)
        if search_keyword != "sample":
            if search_keyword != None:
                print("search keyword is not none or is available")
                if search_keyword.lower() in book.book_title.lower():
                    book_dict = {
                        'title': book.book_title,
                        'section': section.section_title,
                        'author': book.author,
                        'id': book.id,
                        'rating': avg_rating
                        }
                    book_list.append(book_dict)
        else:
            print("search keyword is none or not available")
            book_dict = {
                'title': book.book_title,
                'section': section.section_title,
                'author': book.author,
                'id': book.id,
                'rating': avg_rating
            }
            book_list.append(book_dict)
    #for sections 
    books_section = Book.query.all()
    for book in books_section:
        section = Section.query.get(book.section_id)
        if section.section_title in section_list:
            continue
        section_list.append(section.section_title)
    
    user_id =  session['user_id']
    user = User.query.filter_by(id=user_id).first()
    firstname_ = user.firstname
    userinfo = {"Name": firstname_, 'userid': user_id}
    return render_template('userdash.html', userinfo = userinfo ,book_list = book_list, sections = section_list)

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
                'id': book.id,
                'days remaining': user_book.days_requested - (date.today().day - user_book.date_borrowed.day)
            }
            current_books.append(book_dict)

    # Fetching completed books
    completed_books = []
    user_books = UserBook.query.filter_by(user_id=user_id, status='completed').all()
    for user_book in user_books:
        book = Book.query.get(user_book.book_id)
        section_ = Section.query.get(book.section_id)
        your_rating_ = user_book.rating
        if your_rating_ == None:
            your_rating = "Not Rated"
        else:
            your_rating = your_rating_
        if book:
            book_dict = {
                'title': book.book_title,
                'section': section_.section_title,
                'author': book.author,
                'id': book.id,
                'rating': your_rating
            }
            completed_books.append(book_dict)
    print(completed_books, "this is completed books")
    user_data = {"firstname": firstname_, "userid": user_id}
    user_id =  session['user_id']
    user = User.query.filter_by(id=user_id).first()
    firstname_ = user.firstname
    userinfo = {"Name": firstname_, 'userid': user_id}
    return render_template('userbooks.html', userinfo=userinfo, requestedbooks=requested_books, currentbooks=current_books, completedbooks=completed_books )

@app.route('/user/requestbook', methods=['GET', 'POST'])
def request_book():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        user_id = request.form.get('user_id')
        days_requested = request.form.get('daysRequested')
        print(book_id, user_id, days_requested, "this is book id, user id and days requested")
        # # Add the request to BookRequests database
        if UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='requested').first():
            flash('Request already exists')
            return redirect(url_for('user_books'))
        if UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='accepted').first():
            flash('Book already borrowed')
            return redirect(url_for('user_books'))
        userbooks_entry  = UserBook(user_id=user_id, book_id=book_id, status='requested', paid = False, days_requested=days_requested) 
        new_request = BookRequests(book_id= book_id, user_id=user_id, date = date.today() ,days_requested=days_requested)
        db.session.add(new_request)
        db.session.add(userbooks_entry)
        db.session.commit()
        
        flash('Book request submitted successfully')
        return redirect(url_for('user_books'))


    user_id = session['user_id']
    user_firstname = User.query.get(user_id).firstname
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
    section_id_ = book.section_id
    section = Section.query.get(section_id_)
    book_details = {
        'id' : book.id,
        'title': book.book_title,
        'author': book.author,
        'section': section.section_title,
        'user_id': user_id,
        'user_name': user_firstname
    }
    user_id =  session['user_id']
    user = User.query.filter_by(id=user_id).first()
    firstname_ = user.firstname
    userinfo = {"Name": firstname_, 'userid': user_id}
    return render_template('makerequest.html',userinfo = userinfo ,  book=book_details)


@app.route('/user/return_book/<int:book_id>/<int:user_id>')
def return_book(book_id, user_id):
    if UserBook.query.filter_by(book_id=book_id, user_id=user_id, status='completed').first():
        UserBook.query.filter_by(book_id=book_id, user_id=user_id, status='accepted').delete()
        ub = UserBook.query.filter_by(book_id=book_id, user_id=user_id, status='completed').first()
        ub.times_read += 1
        db.session.commit()
        return redirect(url_for('user_books'))
    user_book = UserBook.query.filter_by(book_id=book_id, user_id=user_id).first()
    if user_book:
        user_book.status = 'completed'
        user_book.date_returned = date.today()
        user_book.times_read += 1
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
        user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id).all()
        for user_book in user_book:
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
        user_id =  session['user_id']
        user = User.query.filter_by(id=user_id).first()
        firstname_ = user.firstname
        userinfo = {"Name": firstname_, 'userid': user_id}
        return render_template('payment.html',userinfo = userinfo, bookDetails = bookDetails, userDetails = userDetails)
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
    

@app.route('/user/ratebook', methods=['GET', 'POST'])
def rate():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    user_id = session['user_id']
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        user_id = user_id
        rating = request.form.get('rating')
        user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id, status = 'completed').first()
        if user_book:
            user_book.rating = rating
            user_book.review = request.form.get('review')
            db.session.commit()
            return redirect(url_for('user_books'))
    book_id = request.args.get('book_id')
    
    if UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='completed', rating="").first():
        book = Book.query.get(book_id)
        if not book:
            flash('Book not found')
            return redirect(url_for('user_dashboard'))
        book = {
            'id': book.id,
            'title': book.book_title,
            'author': book.author,
            'image': book.Image
        }
        user_id = session['user_id']
        user = User.query.get(user_id)
        firstname_ = user.firstname
        userinfo = {"Name": firstname_, 'userid': user_id}
        print("rendering rate")
        return render_template('rate.html', book=book, userinfo=userinfo)
    else:
        flash('Book already rated')
        return redirect(url_for('user_books'))


@app.route('/user/stats')
def user_stats():
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('user_login'))
    user_id = session['user_id']
    user = User.query.get(user_id)
    firstname_ = user.firstname
    user_books = UserBook.query.filter(UserBook.user_id == user_id, UserBook.status.in_(['completed', 'accepted'])).all()
    section_read_bookcount = {}
    for book_ in user_books:
        section_id = Book.query.get(book_.book_id).section_id
        section_name = Section.query.get(section_id).section_title
        if section_name in section_read_bookcount:
            # section_read_bookcount
            section_read_bookcount[section_name] += 1
        else:
            section_read_bookcount[section_name] = 1
    user_details = {"Name": firstname_, 'userid': user_id}
    total_books_read = len(user_books)
    total_books = len(Book.query.all())
    total_books_purchased = len(UserBook.query.filter_by(user_id=user_id, paid=True, status = 'completed').all()) + len(UserBook.query.filter_by(user_id=user_id, paid=True, status = 'accepted').all())
    percentage_of_books_read = (total_books_read/total_books) * 100
    user_stats = {
        'Books Available': total_books,
        'Books Read': total_books_read,
        'Books Purchased': total_books_purchased,
    }
    avg_days_requested = 0
    n= 0
    for book in user_books:
        avg_days_requested += book.days_requested
        n += 1
    if n != 0:
        avg_days = avg_days_requested/n
    else:
        avg_days = 0
    avg_days_ = 0
    if avg_days >= 10:
        avg_days_ = 10
    if avg_days < 10:
        avg_days_ = avg_days
    read_index = (percentage_of_books_read/1000) * avg_days_
    user_percentage = {
        'Total': total_books,
        'Books Read': total_books_read,
        'Percentage of Books Read': percentage_of_books_read,
        'Read Index': read_index
    }
    Most_read_books = UserBook.query.filter_by(user_id=user_id, status='completed').order_by(UserBook.times_read.desc()).limit(5)
    most_read_books = {}
    for book in Most_read_books:
        book_ = Book.query.get(book.book_id)
        section_ = Section.query.get(book_.section_id)
        most_read_books[book_.book_title] = book.times_read
    return render_template('stats-user.html',user_percentage= user_percentage, most_read_books = most_read_books ,userinfo=user_details, section_read_bookcount=section_read_bookcount, userstats = user_stats)

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
            'id': section.id,
            'image': section.Image
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
            
    libinfo_ = Librarian.query.get(session['lib_id'])
    libinfo = {"Name": libinfo_.libraryname}
    return render_template('bookrequests.html',libinfo = libinfo, book_requests=book_request_list , sections = sections_list)

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
        libinfo_ = Librarian.query.get(session['lib_id'])
        libinfo = {"Name": libinfo_.libraryname}
        return render_template('libcurrentbooks.html', libinfo= libinfo ,  books=book_list, sections = sections_)
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
        libinfo_ = Librarian.query.get(session['lib_id'])
        libinfo = {"Name": libinfo_.libraryname}
        return render_template('libcurrentbooks.html',libinfo = libinfo, books=book_list, sections = sections_)    


@app.route('/library/addsection', methods=['GET', 'POST'])
def add_section():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    
    if request.method == 'GET':
        libinfo_ = Librarian.query.get(session['lib_id'])
        libinfo = {"Name": libinfo_.libraryname}
        return render_template('addsection.html', libinfo = libinfo)
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
        libinfo_ = Librarian.query.get(session['lib_id'])
        libinfo = {"Name": libinfo_.libraryname}
        return render_template('addbook.html',libinfo = libinfo )
    if request.method == 'POST':
        section_id = request.args.get('section_id')
        book_title = request.form.get('bookTitle')
        author = request.form.get('author')
        description = request.form.get('Description') #optional
        link = request.form.get('link')
        book_image = request.form.get('bookImage')
        new_book = Book(section_id=section_id, book_title=book_title, author=author, description=description, date_created=date.today(), Image=book_image, link = link)
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
        section_name = Section.query.get(section_id).section_title
        books = Book.query.filter(Book.section_id == section_id).all()
    book_list = []
    for book in books:
        book_dict = {
            'title': book.book_title,
            'author': book.author,
            'content': book.description,
            'image': book.Image
        }
        book_list.append(book_dict)
    libinfo_ = Librarian.query.get(session['lib_id'])
    libinfo = {"Name": libinfo_.libraryname}
    return render_template('showbooks.html',libinfo= libinfo, section_id=section_id, books=book_list, section_name = section_name)

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
        libinfo_ = Librarian.query.get(session['lib_id'])
        libinfo = {"Name": libinfo_.libraryname}
        return render_template('viewdetails.html',libinfo = libinfo,  request_info=book_request_info)
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
    user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id, status= 'requested').first()
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
    user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id, status = 'requested').first()
    if user_book:
        db.session.delete(user_book)
        db.session.delete(book_request)
        db.session.commit()
    else:
        flash('UserBook tuple not found')

    return redirect(url_for('bookrequests'))

@app.route('/library/delete_section')
def delete_section():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    s_id = request.args.get('section_id')
    section = Section.query.get(s_id)
    if section:
        # Delete books with the given section id
        Book.query.filter_by(section_id=s_id).delete()
        
        # Delete requests with the given section id
        BookRequests.query.filter_by(section_id=s_id).delete()
        
        # Delete user books with the given section id
        UserBook.query.filter_by(section_id=s_id).delete()
        
        # Delete the section itself
        db.session.delete(section)
        db.session.commit()
    return redirect(url_for('librarian_dashboard'))

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
    if UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='completed').first():
        UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='accepted').delete()
        ub_ = user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='completed').first()
        ub_.times_read += 1
        db.session.commit()
        return redirect(url_for('current_books'))
    user_book = UserBook.query.filter_by(user_id=user_id, book_id=book_id, status='accepted').first()
    print(user_book, "this is user book")
    if user_book:
        user_book.status = 'completed'
        print("inside user book existsrevoked access")
        user_book.date_returned = date.today()
        db.session.commit()
    return redirect(url_for('current_books'))

@app.route('/library/stats')
def library_stats():
    if 'lib_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('librarian_login'))
    lib_id = session['lib_id']
    librarian = Librarian.query.get(lib_id)
    libname = librarian.libraryname
    sections = Section.query.all()
    section_books = {}
    for section in sections:
        section_books[section.section_title] = len(Book.query.filter_by(section_id=section.id).all())
    total_books = len(Book.query.all())
    total_users = len(User.query.all())
    total_books_read = len(UserBook.query.filter_by(status='completed').all())
    total_books_purchased = len(UserBook.query.filter_by(paid = True).all())
    total_books_requested = len(BookRequests.query.all())
    total_books_granted = len(UserBook.query.filter_by(status='accepted').all())
    lib_info = {"Name": libname}
    #section wise books published
    sections = {}
    for section in Section.query.all():
        sections[section.section_title] = len(Book.query.filter_by(section_id=section.id).all())
    
    #bar chart for total books , books current in read , book requests , books purchased 
    books_stats = {}
    books_stats['Total Books'] = total_books
    books_stats['Books Purchased'] = total_books_purchased
    books_stats['Books Read'] = total_books_read
    books_stats['Books Requested'] = total_books_requested
    books_stats['Books Granted'] = total_books_granted

    # list all total registered users , active users
    users_list = User.query.all()
    users_list_ = {}
    for user in users_list:
        users_list_[user.username] = len(UserBook.query.filter_by(user_id=user.id, status='completed').all()) + len(UserBook.query.filter_by(user_id=user.id, status='accepted').all())
        # users_list_[user.username] = 
    sorted_users_list = {k: v for k, v in sorted(users_list_.items(), key=lambda item: item[1], reverse=True)}

    active_users = 0
    for user in users_list:
        if UserBook.query.filter_by(user_id=user.id, status='completed').first():
            active_users += 1
    #most liked section , most read book , most read author
    most_liked_section = max(section_books, key=section_books.get)
    most_read_book = max(books_stats, key=books_stats.get)
    
    #top rated books
    top_rated_books = UserBook.query.filter_by(status='completed').order_by(UserBook.rating.desc()).limit(5)
    top_rated_books_ = {}
    for book in top_rated_books:
        book_ = Book.query.get(book.book_id)
        top_rated_books_[book_.book_title] = book.rating
    #all availbe user reviews
    user_reviews = UserBook.query.filter_by(status='completed').all()
    user_reviews_ = {}
    for review in user_reviews:
        if review.review != "":
            user_ = User.query.get(review.user_id)
            user_name = user_.firstname
            book_ = Book.query.get(review.book_id)
            user_reviews_[book_.book_title] = [review.review, user_name]
    return render_template('stats-lib.html',top_rated_books = top_rated_books_,user_reviews = user_reviews_ ,  libinfo = lib_info,sections= sections, books_stats = books_stats,users_list = sorted_users_list, active_users = active_users, most_liked_section = most_liked_section, most_read_book = most_read_book)


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