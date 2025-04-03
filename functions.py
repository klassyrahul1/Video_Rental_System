from datetime import datetime, timedelta
from models import User, Movie, Borrow, db
from flask import flash, current_app
from fpdf import FPDF
import os
from fuzzywuzzy import fuzz
from sqlalchemy import func
from flask_mail import Message
import re
import ast

def format_genre(genre_string):
    if not genre_string:
        return "Unknown Genre"
        
    try:
        genre_data = ast.literal_eval(genre_string)
        
        if isinstance(genre_data, list):
            genre_names = [item.get('name', '') for item in genre_data if isinstance(item, dict)]
            return ', '.join(filter(None, genre_names))
        
        elif isinstance(genre_data, dict):
            return genre_data.get('name', 'Unknown Genre')
            
    except (SyntaxError, ValueError):
        pattern = r"'name':\s*'([^']*)'"
        matches = re.findall(pattern, genre_string)
        if matches:
            return ', '.join(matches)
            
    return genre_string if genre_string else "Unknown Genre"


def rent_movie(user_id, movie_id):
    try:
        user_obj = User.query.filter_by(id=user_id).first() 
        movie_obj = Movie.query.filter_by(id=movie_id).first()

        if not user_obj:
            raise ValueError("User not found")
            
        if not movie_obj:
            raise ValueError("Movie not found")

        if user_obj.balance < int(movie_obj.price):
            raise ValueError("Insufficient Balance")
        
        elif int(movie_obj.stock) < 1:
            raise ValueError("Insufficient Quantity in Stock")
        
        else:
            my_order = Borrow(
                user_id=user_obj.id,
                movie_id=movie_id,
                borrow_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=1)
            )

            movie_obj.stock = int(movie_obj.stock) - 1                
            user_obj.balance -= int(movie_obj.price)

            db.session.add(my_order)
            user_obj.lastmovie = movie_obj.title
            db.session.commit()

            flash('Congratulations. Movie Rented Successfully')
            receipt_path = generate_receipt(my_order.id)
            return receipt_path

    except ValueError as e:
        flash(str(e))
        return None
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}")
        db.session.rollback()
        return None
        

def generate_receipt(order_id):
    try:
        order_obj = Borrow.query.filter_by(id=order_id).first()
        if not order_obj:
            flash("Order not found", "error")
            return None
            
        movie_obj = Movie.query.filter_by(id=order_obj.movie_id).first()
        user_obj = User.query.filter_by(id=order_obj.user_id).first()
        
        if order_obj and movie_obj and user_obj:
            receipt = FPDF()
            receipt.add_page()
            
            receipt.set_fill_color(41, 128, 185) 
            receipt.rect(0, 0, 210, 30, 'F')
            receipt.set_font('Arial', 'B', 18)
            receipt.set_text_color(255, 255, 255)  
            receipt.cell(0, 20, 'VRS Movie Rentals', 0, 1, 'C')
            
            receipt.set_font('Arial', 'B', 14)
            receipt.set_text_color(41, 128, 185)  
            receipt.cell(0, 12, 'Official Receipt', 0, 1, 'C')
            
            receipt.set_draw_color(41, 128, 185)  
            receipt.line(10, receipt.get_y(), 200, receipt.get_y())
            receipt.ln(5)
            
            receipt.set_font('Arial', 'B', 12)
            receipt.set_text_color(52, 73, 94)  
            receipt.cell(0, 10, 'Customer Information', 0, 1, 'L')
            
            receipt.set_font('Arial', '', 11)
            receipt.set_text_color(0, 0, 0)  
            receipt.cell(40, 8, 'Customer ID:', 0, 0, 'L')
            receipt.cell(60, 8, f'{order_obj.user_id}', 0, 1, 'L')
            receipt.cell(40, 8, 'Customer Name:', 0, 0, 'L')
            receipt.cell(60, 8, f'{user_obj.name}', 0, 1, 'L')
            
            receipt.ln(5)
            
            receipt.set_font('Arial', 'B', 12)
            receipt.set_text_color(52, 73, 94)  
            receipt.cell(0, 10, 'Order Details', 0, 1, 'L')
            
            receipt.set_font('Arial', '', 11)
            receipt.set_text_color(0, 0, 0) 
            receipt.cell(40, 8, 'Order ID:', 0, 0, 'L')
            receipt.cell(60, 8, f'{order_obj.id}', 0, 1, 'L')
            
            receipt.cell(40, 8, 'Movie Title:', 0, 0, 'L')
            receipt.cell(60, 8, f'{movie_obj.title}', 0, 1, 'L')
            receipt.cell(40, 8, 'Genre:', 0, 0, 'L')
            receipt.cell(60, 8, format_genre(movie_obj.genre), 0, 1, 'L')            
            receipt.cell(40, 8, 'Movie ID:', 0, 0, 'L')
            receipt.cell(60, 8, f'{order_obj.movie_id}', 0, 1, 'L')
            
            try:
                if isinstance(order_obj.borrow_date, str):
                    formatted_date = datetime.strptime(order_obj.borrow_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                else:
                    formatted_date = order_obj.borrow_date.strftime("%Y-%m-%d")
            except ValueError:
                formatted_date = str(order_obj.borrow_date).split()[0] 
                
            receipt.cell(40, 8, 'Rental Date:', 0, 0, 'L')
            receipt.cell(60, 8, f'{formatted_date}', 0, 1, 'L')
            
            receipt.ln(5)
            
            try:
                price = float(movie_obj.price)
            except ValueError:
                price = 0.0 
                
            receipt.set_fill_color(231, 76, 60)  
            receipt.rect(110, receipt.get_y(), 90, 15, 'F')
            
            receipt.set_font('Arial', 'B', 14)
            receipt.set_text_color(255, 255, 255)  
            receipt.cell(110, 15, '', 0, 0, 'L')
            receipt.cell(90, 15, f'Total: ${price:.2f}', 0, 1, 'C')
            
            receipt.ln(10)
            receipt.set_font('Arial', 'I', 11)
            receipt.set_text_color(52, 73, 94)
            receipt.cell(0, 10, 'Thank you for choosing Popcorn Picks!', 0, 1, 'C')

            receipt_dir = os.path.join(current_app.root_path, 'Receipts')
            if not os.path.exists(receipt_dir):
                os.makedirs(receipt_dir, exist_ok=True)
            receipt_path = os.path.join(receipt_dir, f"receipt{order_obj.id}.pdf")
            receipt.output(receipt_path)
            
            return receipt_path
        else:
            flash("Missing order information for receipt generation", "error")
            return None
            
    except Exception as e:
        flash(f"Error generating receipt: {str(e)}", "error")
        print(f"Receipt generation error: {str(e)}") 
        return None
    
def return_movie(order_id, username):
    try:
        user = User.query.filter_by(name=username).first()
        if not user:
            flash("User not found.")
            return False

        order_obj = Borrow.query.filter_by(id=order_id).first()
        if not order_obj:
            flash("Order not found.")
            return False

        if order_obj.returned:
            flash("This movie has already been returned.")
            return False

        movie_obj = Movie.query.filter_by(id=order_obj.movie_id).first()
        if not movie_obj:
            flash("Movie not found in database.")
            return False

        order_obj.returned = True
        movie_obj.stock = int(movie_obj.stock)
        movie_obj.stock += 1
        movie_obj.stock = str(movie_obj.stock)
        print("hi")
        
        db.session.commit()
        
        flash("Movie returned successfully.")
        return True

    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        db.session.rollback()
        return False


def view_orders(user_id):
    try:
        user_obj = User.query.filter_by(id=user_id).first()

        if user_obj is not None:
            return Borrow.query.filter_by(user_id=user_id).all()
        else:
            raise KeyError("User Not Found!")

    except KeyError as e:
        flash(str(e))
    except Exception as e:
        flash(f"An error occurred: {str(e)}")

    return []

def delete_movie_by_title(title):
    try:
        movie_obj = Movie.query.filter_by(title=title).first()

        if movie_obj:
            db.session.delete(movie_obj)
            db.session.commit()
            flash(f"Movie '{title}' deleted successfully!")
            return True
        else:
            flash(f"Movie with title '{title}' not found.")
            return False
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting movie: {str(e)}")
        return False

    
def search_movies(inp):
    try:
        if not inp or len(inp.strip()) == 0:
            return None
            
        exact_match = Movie.query.filter(func.lower(Movie.title) == func.lower(inp)).first()
        if exact_match:
            return exact_match

        substring_matches = Movie.query.filter(func.lower(Movie.title).contains(func.lower(inp))).all()
        if substring_matches:
            return substring_matches

        all_movies = Movie.query.all()
        fuzzy_matches = []

        for movie in all_movies:
            if movie is not None:  
                ratio = fuzz.ratio(inp.lower(), movie.title.lower())
                if ratio > 70:
                    fuzzy_matches.append(movie)

        if fuzzy_matches:
            return fuzzy_matches

        return None
    except Exception as e:
        flash(f"Search error: {str(e)}")
        return None
    
def send_message_to_user(username, message):
    try:
        user = User.query.filter_by(name=username).first()
        if user:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            if user.message:
                user.message = f"{user.message}\n[{timestamp}] {message}"
            else:
                user.message = f"[{timestamp}] {message}"
            
            db.session.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Error sending message: {e}")
        db.session.rollback()
        return Falsec    