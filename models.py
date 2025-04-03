from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['SECRET_KEY'] = '229b845d2e364ca8a032e35c104f69b1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Integer, default=10000)
    borrows = db.relationship('Borrow', backref='user', lazy=True, cascade="all, delete-orphan")
    lastmovie = db.Column(db.String(100))
    message = db.Column(db.String(500), default="")  

    def __init__(self, name, email, password, balance=10000, lastmovie="", message=""):
        self.name = name
        self.email = email
        self.password = password
        self.balance = balance
        self.lastmovie = lastmovie
        self.message = message


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, default=0)
    genre = db.Column(db.String(50))
    rating = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)
    borrows = db.relationship('Borrow', backref='movie', lazy=True, cascade="all, delete-orphan")
    overview = db.Column(db.String(2000))
    poster_path = db.Column(db.String(500))
    year = db.Column(db.String(10), default="01-01-2000")

    def __init__(self, title, genre="", price=0, rating=0.0, stock=0, overview="", poster_path="", year=2000):
        self.title = title
        
        self.genre = genre
        self.price = price if price else 0
        self.rating = rating if rating else 0.0
        self.stock = stock if stock else 0
        self.overview = overview
        self.poster_path = poster_path or "https://img.lovepik.com/background/20211029/medium/lovepik-film-festival-simple-shooting-videotape-poster-background-image_605811936.jpg"
        self.year = year if year else 2000


class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    returned = db.Column(db.Boolean, default=False)  

    def __init__(self, user_id, movie_id, borrow_date=None, deadline=None):
        self.user_id = user_id
        self.movie_id = movie_id
        self.borrow_date = borrow_date or datetime.utcnow()
        self.deadline = deadline or (datetime.utcnow() + timedelta(days=1))
        self.returned = False
