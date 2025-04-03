import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from models import User, Movie, Borrow, db
from functions import (
    format_genre,
    rent_movie,
    return_movie,
    search_movies,
    send_message_to_user,
    delete_movie_by_title
)
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
import re

class TestFunctions(unittest.TestCase):
    def setUp(self):
        """Set up a test database and populate it with hardcoded data."""
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()

            # Add hardcoded users and movies (without specifying IDs)
            user1 = User(name="John Doe", email="john@example.com", password="password", balance=1000)
            user2 = User(name="Jane Doe", email="jane@example.com", password="password", balance=50)

            movie1 = Movie(title="The Matrix", genre="[{'id': 28, 'name': 'Action'}]", price=100, stock=5)
            movie2 = Movie(title="Inception", genre="[{'id': 28, 'name': 'Sci-Fi'}]", price=150, stock=0)

            db.session.add_all([user1, user2, movie1, movie2])
            db.session.commit()

    def tearDown(self):
        """Tear down the test database."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_format_genre(self):
        """Test the genre formatting function."""
        genre_string = "[{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}]"
        result = format_genre(genre_string)
        self.assertEqual(result, "Action, Adventure")

        empty_genre = ""
        result = format_genre(empty_genre)
        self.assertEqual(result, "Unknown Genre")

    @patch('functions.flash')
    def test_rent_movie_success(self, mock_flash):
        """Test successful movie rental."""
        with self.app.app_context():
            # Rent movie for user "John Doe" (balance: 1000) and "The Matrix" (price: 100)
            user = User.query.filter_by(email="john@example.com").first()
            movie = Movie.query.filter_by(title="The Matrix").first()
            
            result = rent_movie(user.id, movie.id)  # Use auto-generated IDs
            self.assertIsNotNone(result)  # Receipt path is returned

            updated_user = User.query.get(user.id)
            updated_movie = Movie.query.get(movie.id)

            self.assertEqual(updated_user.balance, 900)  # Balance deducted
            self.assertEqual(updated_movie.stock, 4)  # Stock reduced

    @patch('functions.flash')
    def test_rent_movie_insufficient_balance(self, mock_flash):
        """Test renting a movie with insufficient balance."""
        with self.app.app_context():
            # Rent movie for user "Jane Doe" (balance: 50) and "The Matrix" (price: 100)
            user = User.query.filter_by(email="jane@example.com").first()
            movie = Movie.query.filter_by(title="The Matrix").first()
            
            result = rent_movie(user.id, movie.id)  # Use auto-generated IDs
            self.assertIsNone(result)  # Rental fails

            updated_user = User.query.get(user.id)
            updated_movie = Movie.query.get(movie.id)

            self.assertEqual(updated_user.balance, 50)  # Balance unchanged
            self.assertEqual(updated_movie.stock, 5)  # Stock unchanged
            mock_flash.assert_called_with("Insufficient Balance")

    @patch('functions.flash')
    def test_rent_movie_out_of_stock(self, mock_flash):
        """Test renting a movie that is out of stock."""
        with self.app.app_context():
            # Rent movie for user "John Doe" (balance: 1000) and "Inception" (stock: 0)
            user = User.query.filter_by(email="john@example.com").first()
            movie = Movie.query.filter_by(title="Inception").first()
            
            result = rent_movie(user.id, movie.id)  # Use auto-generated IDs
            self.assertIsNone(result)  # Rental fails

            updated_user = User.query.get(user.id)
            updated_movie = Movie.query.get(movie.id)

            self.assertEqual(updated_user.balance, 1000)  # Balance unchanged
            self.assertEqual(updated_movie.stock, 0)  # Stock unchanged
            mock_flash.assert_called_with("Insufficient Quantity in Stock")

    @patch('functions.flash')
    def test_return_movie_success(self, mock_flash):
        """Test successfully returning a rented movie."""
        with self.app.app_context():
            # Rent a movie first
            user = User.query.filter_by(email="john@example.com").first()
            movie = Movie.query.filter_by(title="The Matrix").first()
            
            rent_movie(user.id, movie.id)

            borrow = Borrow.query.filter_by(user_id=user.id).first()            
            result = return_movie(borrow.id, user.name)  # Return the rented movie

            updated_borrow = Borrow.query.get(borrow.id)
            updated_movie = Movie.query.get(movie.id)

            self.assertTrue(result)
            self.assertTrue(updated_borrow.returned)  # Marked as returned
            self.assertEqual(updated_movie.stock, 5)  # Stock restored

    @patch('functions.flash')
    def test_return_movie_already_returned(self, mock_flash):
        """Test returning a movie that has already been returned."""
        with self.app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            
            rent_movie(user.id, Movie.query.filter_by(title="The Matrix").first().id)

            borrow = Borrow.query.filter_by(user_id=user.id).first()
            
            return_movie(borrow.id, user.name)  # First return
            result = return_movie(borrow.id, user.name)  # Attempt to return again

            self.assertFalse(result)
            mock_flash.assert_called_with("This movie has already been returned.")

    def test_search_movies_exact_match(self):
        """Test searching for a movie by exact title."""
        with self.app.app_context():
            result = search_movies("The Matrix")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.title, "The Matrix")

    def test_search_movies_no_results(self):
        """Test searching for a non-existent movie."""
        with self.app.app_context():
            result = search_movies("Nonexistent Movie")
            
            self.assertIsNone(result)

    @patch('functions.flash')
    def test_delete_movie_by_title_success(self, mock_flash):
        """Test successfully deleting a movie by title."""
        with self.app.app_context():
            result = delete_movie_by_title("The Matrix")
            
            self.assertTrue(result)

