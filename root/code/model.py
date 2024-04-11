from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=True)
    passhashed = db.Column(db.String(300), nullable=False)

class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=1, unique=True, nullable=False)                                                                                                                                                     
    username = db.Column(db.String(80), unique=True, nullable=False)
    passhashed = db.Column(db.String(300), nullable=False)
    libraryname = db.Column(db.String(200), nullable=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_title = db.Column(db.String(80), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    Image = db.Column(db.String(300), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    book_title = db.Column(db.String(80), unique=True, nullable=False)
    author = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(500), nullable=True)
    link = db.Column(db.String(300), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False)
    Image = db.Column(db.String(300), nullable=True)

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)
    paid = db.Column(db.Boolean, nullable=False)   
    date_borrowed = db.Column(db.DateTime, nullable=True)  
    date_returned = db.Column(db.DateTime, nullable=True)
    days_requested = db.Column(db.Integer, nullable=False)
     

class BookRequests(db.Model):
    #no need of book name , and section id as we can get it from book id
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)  
