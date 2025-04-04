from flask import Flask, redirect, url_for, render_template, request, session
import pickle
from functions import *
from models import app, db, Movie, User, Staff, Borrow
import pandas as pd
from models import User  
from datetime import datetime


with open("rec_model", "rb") as file:
    recommendations = pickle.load(file)


@app.route("/")
def home():
    try:
        if Movie.query.first() is None:
            df = pd.read_csv('/home/klassyrahul/Desktop/VRS/movies_metadata.csv', low_memory=False)
            df['poster_path'] = df['poster_path'].fillna("")  
            df.loc[df['poster_path'].str.startswith("/"), 'poster_path'] = "https://img.lovepik.com/background/20211029/medium/lovepik-film-festival-simple-shooting-videotape-poster-background-image_605811936.jpg"

            for index, row in df.iterrows():
                movie = Movie(
                    title=row['title'],
                    year=row['release_date'],
                    genre=row['genres'],
                    poster_path=row['poster_path'],
                    overview=row['overview'],
                    stock=10,
                    price=100
                )
                db.session.add(movie)
                
                if index % 100 == 0:
                    db.session.commit()
            
            db.session.commit()
    except Exception as e:
        print(f"Error loading movies: {e}")
        db.session.rollback()  

    return render_template("login_user.html")


@app.route("/login", methods=['POST', 'GET'])
def login_user():
    if request.method == 'POST':
        Username = request.form.get('username', 'default_admin_username')
        session['username'] = Username
        Password = request.form.get('password', '')
    
        user = User.query.filter_by(name=Username).first()
        if user is not None and Password == user.password:
            return redirect(url_for('home_page'))
        else:
            return render_template("login_user.html", warn="y")
    
    return render_template("login_user.html", warn="n")


@app.route("/home")
def home_page():
    if 'username' in session and session['username'] is not None:
        username = session['username']
        user = User.query.filter_by(name=username).first()
        if user is not None:
            lastmovie = user.lastmovie if user.lastmovie is not None else "Jumanji"
            titles = recommendations.get(lastmovie, [])
            links = []
            genres = []
            for movie in titles:
                movie_obj = Movie.query.filter_by(title=movie).first()
                if movie_obj:
                    links.append(movie_obj.poster_path)
                    genres.append(format_genre(movie_obj.genre))
            
            all_genres = get_all_genres()
            
            return render_template("home.html", movie_titles=titles, movie_links=links, movie_genres=genres, all_genres=all_genres, length=len(links), user=username)
    
    return redirect(url_for('login_user'))


def get_all_genres():
    all_movies = Movie.query.all()
    genre_set = set()
    
    for movie in all_movies:
        if movie is not None:
            if movie.genre:
                movie_genres = format_genre(movie.genre).split(', ')
                for genre in movie_genres:
                    if genre.strip():
                        genre_set.add(genre.strip())
    
    return sorted(list(genre_set))


@app.route("/filter_genre", methods=['POST'])
def filter_genre():
    if 'username' not in session:
        return redirect(url_for('login_user'))
        
    username = session['username']
    selected_genre = request.form.get('genre', '')
    
    if selected_genre == 'All':
        return redirect(url_for('home_page'))
    
    filtered_movies = []
    all_movies = Movie.query.all()
    
    for movie in all_movies:
        if movie is not None:
            if movie.genre and selected_genre in format_genre(movie.genre):
                filtered_movies.append(movie)
    
    titles = [movie.title for movie in filtered_movies]
    links = [movie.poster_path for movie in filtered_movies]
    genres = [format_genre(movie.genre) for movie in filtered_movies]
    all_genres = get_all_genres()
    
    return render_template("home.html", movie_titles=titles, movie_links=links, movie_genres=genres, all_genres=all_genres, length=len(links), user=username, selected_genre=selected_genre)


@app.route("/login_staff", methods=['POST', 'GET'])
def login_staff():
    if request.method == 'POST':
        Username = request.form.get('username', '')
        Password = request.form.get('password', '')
        staff = Staff.query.filter_by(name=Username).first()
        
        if staff is not None:
            if Password == staff.password:
                orders = Borrow.query.all()
                titles = []
                deadline = []
                uname = []
                uemail = []
                
                for order in orders:
                    movie = Movie.query.filter_by(id=order.movie_id).first()
                    user = User.query.filter_by(id=order.user_id).first()
                    if movie and user:
                        titles.append(movie.title)
                        deadline.append(order.deadline)
                        uname.append(user.name)
                        uemail.append(user.email)
                
                length = len(uname)
                return render_template("staff.html", titles=titles, deadline=deadline, uname=uname, uemail=uemail, length=length)
            else:
                return render_template("login_staff.html", warn="y")
        else:
            return render_template("login_staff.html", warn="y")
            
    return render_template("login_staff.html", warn="n")


@app.route("/login_manager", methods=['POST', 'GET'])
def login_manager():
    if request.method == 'POST':
        Password = request.form.get('password', '')
        if Password == "admin":
            return render_template("manager.html")
        else:
            return render_template("login_manager.html", warn="y")
    return render_template("login_manager.html", warn="n")


@app.route("/register", methods=['POST', 'GET'])
def create_acc():
    if request.method == 'POST':
        Username = request.form.get('username', '')
        session['username'] = Username
        Designation = request.form.get('role', '')
        email = request.form.get('email', '')
        Password = request.form.get('password', '')
        repassword = request.form.get('confirm-password', '')
        
        if Password == repassword:
            if Designation == 'User':
                user = User(name=Username, email=email, password=Password, lastmovie="Jumanji", balance=1000)
                db.session.add(user)
                try:
                    db.session.commit()
                    
                    lastmovie = "Jumanji"
                    titles = recommendations.get(lastmovie, [])
                    links = []
                    genres = []
                    for movie in titles:
                        movie_obj = Movie.query.filter_by(title=movie).first()
                        if movie_obj:
                            links.append(movie_obj.poster_path)
                            genres.append(format_genre(movie_obj.genre))
                    
                    all_genres = get_all_genres()
                    
                    return render_template("home.html", movie_titles=titles, movie_links=links, movie_genres=genres, all_genres=all_genres, length=len(links), user=Username)
                except Exception as e:
                    print(f"Error adding user: {e}")
                    db.session.rollback()
                    return render_template("register.html", warn="error")
            
            elif Designation == 'Staff':
                staff = Staff(name=Username, email=email, password=Password)
                db.session.add(staff)
                try:
                    db.session.commit()
                    orders = Borrow.query.all()
                    titles = []
                    deadline = []
                    uname = []
                    uemail = []
                    
                    for order in orders:
                        movie = Movie.query.filter_by(id=order.movie_id).first()
                        user = User.query.filter_by(id=order.user_id).first()
                        if movie and user:
                            titles.append(movie.title)
                            deadline.append(order.deadline)
                            uname.append(user.name)
                            uemail.append(user.email)
                    
                    length = len(uname)
                    return render_template('staff.html', titles=titles, deadline=deadline, uname=uname, uemail=uemail, length=length)
                except Exception as e:
                    print(f"Error adding staff: {e}")
                    db.session.rollback()
                    return render_template("register.html", warn="error")
        else:
            return render_template("register.html", warn="y")
    
    return render_template("register.html", warn="n")


@app.route("/delete_user", methods =['POST','GET'])
def delete_user():
    success = None
    message = None
    
    if request.method == 'POST':
        Username = request.form['username']
        Designation = request.form['user_cat']
        
        if Designation == 'User':
            user = User.query.filter_by(name=Username).first()
            if user:
                try:
                    User.query.filter_by(name=Username).delete()
                    db.session.commit()
                    success = True
                    message = f"User '{Username}' was successfully deleted."
                except Exception as e:
                    db.session.rollback()
                    success = False
                    message = f"Error deleting user: {str(e)}"
            else:
                success = False
                message = f"User '{Username}' not found."
                
        elif Designation == 'Staff':
            staff = Staff.query.filter_by(name=Username).first()
            if staff:
                try:
                    Staff.query.filter_by(name=Username).delete()
                    db.session.commit()
                    success = True
                    message = f"Staff '{Username}' was successfully deleted."
                except Exception as e:
                    db.session.rollback()
                    success = False
                    message = f"Error deleting staff: {str(e)}"
            else:
                success = False
                message = f"Staff '{Username}' not found."
                
    return render_template("delete_user.html", success=success, message=message)


@app.route("/manager", methods=['POST', 'GET'])
def manager():
    success = None
    message = None
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        if title:
            try:
                result = delete_movie_by_title(title)
                if result:
                    success = True
                    message = f"Movie '{title}' deleted successfully!"
                else:
                    success = False
                    message = f"Movie with title '{title}' not found."
            except Exception as e:
                success = False
                message = f"Error deleting movie: {str(e)}"
        else:
            success = False
            message = "No movie title provided."
    
    return render_template("manager.html", success=success, message=message)


@app.route("/staff", methods=['POST', 'GET'])
def staff():
    return render_template("staff.html")

@app.route("/customer", methods=['POST', 'GET'])
def customer():
    if 'username' not in session:
        return redirect(url_for('login_user'))
        
    username = session['username']
    now = datetime.now()
    user = User.query.filter_by(name=username).first()
    rentals = Borrow.query.filter_by(user_id=user.id, returned=False).all()
    titles = []
    id_list = []
    borrow_date = []
    deadline = []
    
    for rental in rentals:
        movie = Movie.query.filter_by(id=rental.movie_id).first()
        if movie:
            titles.append(movie.title)
            id_list.append(rental.id)
            borrow_date.append(rental.borrow_date)
            deadline.append(rental.deadline)
    
    length = len(titles)
    balance = user.balance
    
    if request.method == "POST":
        if 'amount' in request.form:
            try:
                amount = int(request.form.get('amount', 0))
                if amount > 0:
                    user.balance += amount
                    db.session.commit()
                    flash(f"${amount} added to your account successfully.")
                    return redirect(url_for('customer'))
                else:
                    flash("Please enter a positive amount.")
            except ValueError:
                flash("Invalid amount entered.")
    
    messages = user.message.split('\n') if user.message else []
    has_messages = len(messages) > 0
    
    return render_template("customer.html", id=id_list, balance=balance, titles=titles, borrow_date=borrow_date, deadline=deadline, length=length, user=username, has_messages=has_messages, messages=messages, now=now)
    
@app.route('/search', methods=['GET', 'POST'])
def search():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login_user'))
    
    username = session['username']
    
    # Get current user
    user_obj = User.query.filter_by(name=username).first()
    
    # Initialize recently viewed in session if not present
    if 'recently_viewed' not in session:
        session['recently_viewed'] = []
        
        # If user has a last movie viewed, add it to session
        if user_obj and user_obj.lastmovie:
            last_movie = Movie.query.filter_by(title=user_obj.lastmovie).first()
            if last_movie:
                movie_entry = {
                    'title': last_movie.title,
                    'poster_path': last_movie.poster_path
                }
                session['recently_viewed'].append(movie_entry)
    
    if request.method == 'POST':
        inp = request.form.get('inp', '')
        result = search_movies(inp)

        # Get recently viewed movies for this user
        recently_viewed = session.get('recently_viewed', [])
        
        if result is None:
            return render_template('blank_search.html', input=inp, movie_links=inp, user=username, recently_viewed=recently_viewed)
        
        if isinstance(result, list):
            result = [movie for movie in result if movie is not None]
            movie_links = [movie.poster_path for movie in result]
            movie_titles = [movie.title for movie in result]
            length = len(result)
        else:
            movie_links = [result.poster_path]
            movie_titles = [result.title]
            length = 1
        
        # Render the search results page
        return render_template('search.html', 
                              input=inp, 
                              movie_links=movie_links,
                              movie_titles=movie_titles, 
                              length=length, 
                              user=username,
                              recently_viewed=recently_viewed)
    
    # Get recently viewed movies for this user
    recently_viewed = session.get('recently_viewed', [])
    
    return render_template('search.html', 
                          input="", 
                          movie_links=[], 
                          length=0, 
                          user=username,
                          recently_viewed=recently_viewed)

@app.route('/rent/<title>', methods=['POST', 'GET'])
def rent(title):
    if 'username' not in session:
        return redirect(url_for('login_user'))
    
    username = session['username']
    user_obj = User.query.filter_by(name=username).first()
    if not user_obj:
        return render_template("error.html", message="User not found.")
    
    movie = Movie.query.filter_by(title=title).first()
    if not movie:
        return render_template("error.html", message="Movie not found.")
    
    user_obj.lastmovie = title
    db.session.commit()
    if 'recently_viewed' not in session:
        session['recently_viewed'] = []
        
    movie_entry = {
        'title': movie.title,
        'poster_path': movie.poster_path
    }
    
    session['recently_viewed'] = [m for m in session['recently_viewed'] if m.get('title') != movie.title]
    session['recently_viewed'].insert(0, movie_entry)
    session['recently_viewed'] = session['recently_viewed'][:4]
    session.modified = True
    
    price = movie.price
    genre = movie.genre
    
    try:
        genre_names_string = format_genre(genre)
    except:
        genre_names_string = "Unknown Genre"
        
    overview = movie.overview
    poster_path = movie.poster_path
    rating = movie.rating
    stock = movie.stock
    
    if request.method == 'POST':
        if stock == 0:
            return render_template("rent.html", title=title, price=str(price), genre=genre_names_string, overview=overview, poster_path=str(poster_path), rating=str(rating), stock=str(stock), warn="ystock", user=username)
        
        if user_obj.balance < int(price):
            return render_template("rent.html", title=title, price=str(price), genre=genre_names_string, overview=overview, poster_path=str(poster_path), rating=str(rating), stock=str(stock), warn="ybalance", user=username)
        
        rent_result = rent_movie(user_obj.id, movie.id)
        return redirect(url_for('customer'))
    
    return render_template("rent.html", title=title, price=str(price), genre=genre_names_string, overview=overview, poster_path=str(poster_path), rating=str(rating), stock=str(stock), warn="n", user=username)


@app.route('/return_movie', methods=['POST', 'GET'])
def handle_return_movie():
    rental_id = request.form.get('order_id')
    
    if 'username' not in session:
        return redirect(url_for('login_user'))
        
    username = session['username']
    
    if not rental_id:
        flash("Missing order ID.")
        return redirect(url_for('customer'))

    try:
        rental_id = int(rental_id)
    except ValueError:
        flash("Invalid order ID.")
        return redirect(url_for('customer'))
    
    success = return_movie(rental_id, username)
    
    return redirect(url_for('customer'))


@app.route("/add_credit", methods=['POST'])
def add_credit():
    if 'username' not in session:
        return redirect(url_for('login_user'))
        
    username = session['username']
    
    if request.method == 'POST':
        amount = request.form.get('amount', 0)
        try:
            amount = int(amount)
            if amount <= 0:
                return render_template("error.html", message="Please enter a positive amount.")
                
            user = User.query.filter_by(name=username).first()
            if user:
                user.balance += amount
                db.session.commit()
                
                return redirect(url_for('customer'))
            else:
                return render_template("error.html", message="User not found.")
        except ValueError:
            return render_template("error.html", message="Invalid amount entered.")
    
    return redirect(url_for('customer'))

@app.route("/send_message", methods=['POST'])
def send_message():
    if request.method == 'POST':
        recipient = request.form.get('username', '')
        message = request.form.get('message', '')
        orders = Borrow.query.all()
        titles = []
        deadline = []
        uname = []
        uemail = []
        
        for order in orders:
            movie = Movie.query.filter_by(id=order.movie_id).first()
            user = User.query.filter_by(id=order.user_id).first()
            if movie and user:
                titles.append(movie.title)
                deadline.append(order.deadline)
                uname.append(user.name)
                uemail.append(user.email)
        
        length = len(uname)
        
        if recipient and message:
            result = send_message_to_user(recipient, message)
            if result:
                return render_template("staff.html", titles=titles, deadline=deadline, uname=uname, uemail=uemail, length=length, message_status="Message sent successfully!")
            else:
                return render_template("staff.html", titles=titles, deadline=deadline, uname=uname, uemail=uemail, length=length, message_status="Error: User not found.")
        else:
            return render_template("staff.html", titles=titles, deadline=deadline, uname=uname, uemail=uemail, length=length, message_status="Error: Missing username or message.")
    
    return redirect(url_for('login_staff'))

@app.route("/view_messages")
def view_messages():
    if 'username' not in session:
        return redirect(url_for('login_user'))
        
    username = session['username']
    
    user = User.query.filter_by(name=username).first()
    if user:
        messages = user.message.split('\n') if user.message else []
        return render_template("messages.html", messages=messages, user=username)
    
    return redirect(url_for('login_user'))


if __name__ == "__main__":
    app.secret_key = "movie_rental_system_secret_key"
    app.run(debug=True)

