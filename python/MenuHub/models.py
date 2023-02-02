from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash


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
