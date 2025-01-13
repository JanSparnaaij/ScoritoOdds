from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User Model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        """Hash the user's password"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check the user's password"""
        return check_password_hash(self.password, password)
