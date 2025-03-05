# DataBase/Models/__init__.py

# from flask_sqlalchemy import SQLAlchemy
# from .usermodels import User, OAuthUser, PasswordResetToken
# from .memorychatbotmode import Conversation, Message

# # Initialize the db object to be used in the models
# db = SQLAlchemy()
from .database import db  # Import db from database.py
from .usermodels import User, OAuthUser, PasswordResetToken
from .memorychatbotmode import Conversation, Message
