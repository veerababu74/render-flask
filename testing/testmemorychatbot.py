from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import os

app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = "your_secret_key"  # Change this to a secure random key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = (
    "your_jwt_secret_key"  # Change this to a secure random key
)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Google API Key
GOOGLE_API_KEY = (
    "AIzaSyDSHVpGQfM_8JBrfZO4bQ6r4exhj-XmR2Y"  # Replace with your actual API key
)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # "user" or "ai"
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id"), nullable=False
    )


def history_to_messages(conversation_id):
    messages = (
        Message.query.filter_by(conversation_id=conversation_id)
        .order_by(Message.id.desc())  # Order by most recent first
        .limit(20)  # Limit to 20 messages
        .all()
    )
    # Reverse the order to display oldest to newest
    messages = reversed(messages)
    # Format the messages as { "role": "human", "content": "" } or { "role": "ai", "content": "" }
    chat_history = []
    user_message = None  # To store the last user message
    for msg in messages:
        if msg.role == "user":
            user_message = {"role": "human", "content": msg.content}
        elif msg.role == "ai" and user_message:
            # Append the user message first, then the bot's response
            chat_history.append(user_message)
            chat_history.append({"role": "ai", "content": msg.content})
            user_message = None  # Reset user_message after pairing
    return chat_history


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Account created successfully!"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@app.route("/api/conversations", methods=["GET"])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": c.id, "title": c.title} for c in conversations]), 200


@app.route("/api/conversation/<int:conversation_id>", methods=["GET"])
@jwt_required()
def view_conversation(conversation_id):
    user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    messages = Message.query.filter_by(conversation_id=conversation.id).all()
    return (
        jsonify(
            {
                "conversation": {"id": conversation.id, "title": conversation.title},
                "messages": [
                    {"id": m.id, "role": m.role, "content": m.content} for m in messages
                ],
            }
        ),
        200,
    )


@app.route("/api/create_conversation", methods=["POST"])
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    new_conversation = Conversation(title="New Chat", user_id=user_id)
    db.session.add(new_conversation)
    db.session.commit()
    return jsonify({"conversation_id": new_conversation.id, "title": "New Chat"}), 201


@app.route("/api/delete_conversation/<int:conversation_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conversation_id):
    user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    Message.query.filter_by(conversation_id=conversation.id).delete()
    db.session.delete(conversation)
    db.session.commit()
    return jsonify({"message": "Conversation deleted successfully"}), 200


@app.route("/api/get_response", methods=["POST"])
@jwt_required()
def get_response():
    user_id = get_jwt_identity()
    data = request.get_json()
    user_message = data.get("message")
    conversation_id = data.get("conversation_id")

    if not conversation_id:
        new_conversation = Conversation(title="New Chat", user_id=user_id)
        db.session.add(new_conversation)
        db.session.commit()
        conversation_id = new_conversation.id

    user_msg = Message(
        content=user_message, role="user", conversation_id=conversation_id
    )
    db.session.add(user_msg)
    db.session.commit()

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY
        )
        chat_history = history_to_messages(conversation_id)
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful AI assistant."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )
        contextualize_chain = qa_prompt | llm | StrOutputParser()
        bot_response = contextualize_chain.invoke(
            {"chat_history": chat_history, "input": user_message}
        )
        bot_response = (
            bot_response.content
            if hasattr(bot_response, "content")
            else str(bot_response)
        )
    except Exception as e:
        bot_response = f"Error: {str(e)}"

    bot_msg = Message(content=bot_response, role="ai", conversation_id=conversation_id)
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({"response": bot_response, "conversation_id": conversation_id}), 200


@app.route("/api/update_title", methods=["POST"])
@jwt_required()
def update_title():
    user_id = get_jwt_identity()
    data = request.get_json()
    conversation_id = data.get("conversation_id")
    new_title = data.get("title")

    if not conversation_id or not new_title:
        return jsonify({"error": "Missing required fields"}), 400

    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    conversation.title = new_title
    db.session.commit()
    return (
        jsonify(
            {"success": True, "conversation_id": conversation_id, "title": new_title}
        ),
        200,
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
