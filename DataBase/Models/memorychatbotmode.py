# from DataBase.Models import db  # Import db from __init__.py
from DataBase.Models.database import db


class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # Title of the conversation

    # Correct the foreign key to reference the 'users' table
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Use a string-based reference to avoid circular imports
    messages = db.relationship("Message", backref="conversation", lazy=True)

    def __repr__(self):
        return f"<Conversation {self.title} by User {self.user_id}>"


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'

    # Foreign key to reference the conversation
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.id"), nullable=False
    )

    def __repr__(self):
        return f"<Message {self.id} in Conversation {self.conversation_id}>"
