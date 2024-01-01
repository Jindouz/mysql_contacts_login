from flask import Flask, render_template, request, redirect, flash, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:SECRET@localhost/contacts' #replace SECRET with your MySQL password
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Define Contact model
class Contacts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    tel = db.Column(db.String(20), nullable=False)
    picture = db.Column(db.String(255), nullable=True)


# Load user from database
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Home page
@app.route('/')
def index():
    # Display all contacts
    if current_user.is_authenticated:
        contacts = Contacts.query.all()
        return render_template('index.html', contacts=contacts, user=current_user)

    flash('Please log in to access the home page.', 'info')
    return redirect('/login')


# Register a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Check if the username already exists
        existing_user = Users.query.filter_by(username=username).first()

        if existing_user:
            flash('Username is already taken. Please choose a different one.', 'danger')
        else:
            new_user = Users(username=username, password=hashed_password)

            try:
                # Use a single transaction to add the new user and commit
                db.session.add(new_user)
                db.session.commit()

                session['user_id'] = new_user.id

                flash('Registration successful! Please log in.', 'success')
                return redirect('/login')

            except:
                # Handle other potential errors during registration
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')

    dummy_user = {'is_authenticated': False}
    return render_template('register.html', user=dummy_user)



# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        user = Users.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password_candidate):
            login_user(user)  # This logs in the user and updates current_user
            flash('Login successful!', 'success')
            return redirect('/')

        flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html', user=current_user)


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Logs out the current user
    flash('You have been logged out.', 'success')
    return redirect('/login')


# Add a new contact
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        tel = request.form['tel']
        picture = request.form['picture']

        new_contact = Contacts(name=name, email=email, tel=tel, picture=picture)
        db.session.add(new_contact)
        db.session.commit()

        flash('Contact added successfully!', 'success')
        return redirect('/')

    return render_template('add.html', user=current_user)

# Edit an existing contact
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    contact = Contacts.query.get(id)

    if request.method == 'POST':
        contact.name = request.form['name']
        contact.email = request.form['email']
        contact.tel = request.form['tel']
        contact.picture = request.form['picture']

        db.session.commit()

        flash('Contact updated successfully!', 'success')
        return redirect('/')

    return render_template('edit.html', contact=contact, user=current_user)


# Delete a contact
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    contact = Contacts.query.get(id)
    db.session.delete(contact)
    db.session.commit()

    flash('Contact deleted successfully!', 'success')
    return redirect('/')

# Function to create tables
def create_tables():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
