# PACKAGES
import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import MetaData
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"sqlite:///{os.path.join(basedir, 'menuhub.sqlite')}"
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False

Bootstrap(app)

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

login = LoginManager()
login.init_app(app)

# MODELS


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True,
                      nullable=False, name='email_unique_constraint')
    password_hash = db.Column(db.String(128), nullable=False)
    admin = db.Column(db.Boolean)

    def __repr__(self):
        return f'<User {self.name}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False,
                     name='restaurant_name_unique_constraint')
    dishes = db.relationship(
        'Dish', backref='dish_owner', lazy=True)

    def __repr__(self):
        return f'<Restaurant {self.name}>'


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey(
        'restaurant.id'), nullable=False)

    def __repr__(self):
        return f"Dish: #{self.id}, name: {self.name}"


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# ROUTES


@app.route("/index")
@app.route("/home")
@app.route('/index', methods=["POST"])
@app.route('/home', methods=["POST"])
@login_required
def index():
    if request.method == "POST":
        dish_name = request.form['dish_name']
        price = request.form['price']
        category = request.form['category']
        restaurant_id = request.form['restaurant']

        new_dish = Dish(name=dish_name, category=category,
                        price=price, restaurant_id=restaurant_id)

        try:
            db.session.add(new_dish)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_message = str(e.orig)
            flash('danger', error_message)
            return redirect(url_for('index'))

        flash('success', 'Success! The dish was added.')
        return redirect(url_for('index'))
    else:
        dishes = Dish.query.order_by(Dish.price).all()
        restaurant = Restaurant.query.order_by(Restaurant.name).all()
        return render_template('index.html', dishes=dishes, restaurants=restaurant)



@app.route('/')
@app.route('/login')
@app.route('/', methods=['POST'])
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['userPassword']
        registered_user = User.query.filter_by(email=email).first()
        if registered_user is None:
            flash('danger', 'Invalid e-mail')
            return redirect(url_for('login'))
        if User.check_password(registered_user, password):
            login_user(registered_user)
            return redirect(url_for('index'))
        flash('danger', 'Invalid password')
        return redirect(url_for('login'))
    return render_template("login.html")


@app.route('/register')
@app.route('/register', methods=['POST'])
def register():
    if request.method == "POST":
        name = request.form['userName']
        email = request.form['email']
        password = request.form['userPassword']
        admin = False
        if 'isAdmin' in request.form:
            admin = True

        hashed_password = generate_password_hash(password)

        new_user = User(name=name, email=email,
                        password_hash=hashed_password, admin=admin)

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_message = str(e.orig)
            flash('danger', error_message)
            return redirect(url_for('register'))

        flash('success', 'Success! The user was registred.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/restaurants')
@app.route('/restaurants', methods=['POST'])
@login_required
def restaurants():
    if request.method == "POST":
        name = request.form['restaurantName']

        new_restaurant = Restaurant(name=name)

        try:
            db.session.add(new_restaurant)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_message = str(e.orig)
            flash('danger', error_message)
            return redirect(url_for('restaurants'))

        flash('success', 'Success! The restaurant was registred.')
        return redirect(url_for('index'))
    return render_template('restaurants.html')


@app.route('/update_dish/<dish_id>')
@app.route('/update_dish', methods=['POST'])
@login_required
def update_dish(dish_id=None):
    if request.method == "POST":
        id = request.form['dish_id']
        name = request.form['dish_name']
        price = request.form['price']
        category = request.form['category']

        dish = Dish.query.get(id)
        dish.name = name
        dish.price = price
        dish.category = category

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_message = str(e.orig)
            flash('danger', error_message)
            return render_template('update_dish.html', dish=dish)

        flash('success', 'Success! The dish was updated.')
        return redirect(url_for('index'))
    else:
        dish = Dish.query.filter_by(id=dish_id).first()
        return render_template('update_dish.html', dish=dish)


@app.route('/delete_dish/<dish_id>')
@login_required
def delete_dish(dish_id):
    dish = Dish.query.get(dish_id)

    try:
        db.session.delete(dish)
        db.session.commit()
        flash('success', 'Success! The dish was deleted.')
    except IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig)
        flash('danger', error_message)

    return redirect(url_for('index'))