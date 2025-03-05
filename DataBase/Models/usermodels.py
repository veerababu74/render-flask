# from DataBase.Models import db  # Import db from __init__.py
from flask_bcrypt import Bcrypt
from DataBase.Models.database import db
import re

# Initialize bcrypt
bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    firstname = db.Column(db.String(120), nullable=False)
    lastname = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)  # New field
    oauth_users = db.relationship("OAuthUser", backref="user", lazy=True)
    reset_tokens = db.relationship("PasswordResetToken", backref="user", lazy=True)
    conversations = db.relationship("Conversation", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    @staticmethod
    def validate_password(password):
        """Validate password strength."""
        if len(password) < 6:
            return False  # Password too short
        if not re.search(r"[A-Z]", password):
            return False  # No capital letter found
        if not re.search(r"[\W_]", password):  # No special character found
            return False
        return True


class OAuthUser(db.Model):
    __tablename__ = "oauth_users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    oauth_provider = db.Column(db.String(50), nullable=False)  # e.g., 'google'
    oauth_id = db.Column(
        db.String(120), unique=False, nullable=False
    )  # OAuth unique ID

    def __repr__(self):
        return f"<OAuthUser {self.oauth_provider} {self.oauth_id}>"


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    used = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<PasswordResetToken for User {self.user_id} Used: {self.used}>"
