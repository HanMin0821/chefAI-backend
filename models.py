from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    recipes = db.relationship('Recipe', backref='author', lazy=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        # Use a PBKDF2 variant that's broadly supported (avoid scrypt)
        # Some Python/OpenSSL builds (e.g. LibreSSL on macOS) do not
        # expose hashlib.scrypt, which newer werkzeug may try to use.
        # Explicitly request pbkdf2:sha256 for compatibility.
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)  # Stored as JSON string
    missing_ingredients = db.Column(db.Text, nullable=True) # Stored as JSON string
    steps = db.Column(db.Text, nullable=False)        # Stored as JSON string
    nutrition = db.Column(db.Text, nullable=True)     # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recipe {self.title}>'

