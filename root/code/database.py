from app import app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=True)
    passhashed = db.Column(db.String(300), nullable=False)
    library_id = db.Column(db.Integer, db.ForeignKey('librarian.id'), nullable=False)

class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)                                                                                                                                                     
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    passhashed = db.Column(db.String(300), nullable=False)
    firstname = db.Column(db.String(80), nullable=True)
    lastname = db.Column(db.String(80), nullable=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey('librarian.id'), nullable=False)
    section_title = db.Column(db.String(80), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    Image = db.Column(db.String(300), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey('librarian.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    book_title = db.Column(db.String(80), unique=True, nullable=False)
    author = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(500), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False)
    Image = db.Column(db.String(300), nullable=True)

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    library_id = db.Column(db.Integer, db.ForeignKey('librarian.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)

