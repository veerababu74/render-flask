from flask import Flask, request, jsonify, Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from DataBase.Models.database import db
from DataBase.Models.memorychatbotmode import Message, Conversation
from DataBase.Models.usermodels import User
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import os
from Properties.urls import FRONTEND_BASE_URL_FOR_CORS

memory_chatbot_blueprint = Blueprint("memory_chatbot", __name__)


# Google API Key
GOOGLE_API_KEY = "AIzaSyDSHVpGQfM_8JBrfZO4bQ6r4exhj-XmR2Y"


def history_to_messages(conversation_id):
    messages = (
        Message.query.filter_by(conversation_id=conversation_id)
        .order_by(Message.id.desc())
        .limit(20)
        .all()
    )
    messages = reversed(messages)

    chat_history = []
    user_message = None

    for msg in messages:
        if msg.role == "user":
            user_message = {"role": "human", "content": msg.content}
        elif msg.role == "ai" and user_message:
            chat_history.append(user_message)
            chat_history.append({"role": "ai", "content": msg.content})
            user_message = None
    return chat_history


@memory_chatbot_blueprint.route("/api/get_response", methods=["POST"])
@jwt_required()
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
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


@memory_chatbot_blueprint.route("/api/conversations", methods=["GET"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": c.id, "title": c.title} for c in conversations]), 200


@memory_chatbot_blueprint.route(
    "/api/conversation/<int:conversation_id>", methods=["GET"]
)
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
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


@memory_chatbot_blueprint.route("/api/create_conversation", methods=["POST"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    new_conversation = Conversation(title="New Chat", user_id=user_id)
    db.session.add(new_conversation)
    db.session.commit()
    return jsonify({"conversation_id": new_conversation.id, "title": "New Chat"}), 201


@memory_chatbot_blueprint.route(
    "/api/delete_conversation/<int:conversation_id>", methods=["DELETE"]
)
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
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


@memory_chatbot_blueprint.route("/api/update_title", methods=["POST"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
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
