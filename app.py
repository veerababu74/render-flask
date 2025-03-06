import os
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth


from config import configure_app
from DataBase.Models.database import db
from UserProfile.userdetails import user_bp
from Authentication.EmailAuth.emial import email_bp
from Authentication.SocialAuth.Github import github_bp
from Authentication.EmailAuth.passwordreset import email_pass_reset_bp
from Authentication.SocialAuth.Auth import oauth
from Authentication.EmailAuth.mailAuth import mail
from MemoryChatBot.routes import memory_chatbot_blueprint

# Create the Flask app instance
app = Flask(__name__)

# Enable CORS for frontend interactions

from Properties.urls import FRONTEND_BASE_URL_FOR_CORS, FRONTEND_BASE_URL

# CORS(
#     app,
#     resources={
#         r"/*": {"origins": FRONTEND_BASE_URL_FOR_CORS, "supports_credentials": True}
#     },
# )

configure_app(app)
CORS(app, resources={r"/*": {"origins": app.config["CORS_ALLOWED_ORIGINS"]}})
# CORS(app)
# Configure the app using the configuration function


# Initialize Flask extensions
db.init_app(app)
oauth.init_app(app)
mail.init_app(app)
jwt_manager = JWTManager()
jwt_manager.init_app(app)
# Initialize the Migrate object
migrate = Migrate()
migrate.init_app(app, db)  # Initialize migrations with app and db


# Example route to test if the app is working
@app.route("/")
def home():
    return jsonify(
        {"message": "Welcome to the Flask App!", "environment": app.config["ENV"]}
    )


@app.route("/hello")
def hello():
    return jsonify(
        {
            "message": "Welcome to the Flask App! your email verified",
            "environment": app.config["ENV"],
        }
    )


# @app.after_request
# def add_cors_headers(response):
#     response.headers["Access-Control-Allow-Origin"] = FRONTEND_BASE_URL_FOR_CORS
#     response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
#     response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
#     response.headers["Access-Control-Allow-Credentials"] = "true"
#     return response


# Ensure the SQLite database file and structure exist in development
# if app.config["ENV"] == "development":
#     with app.app_context():
#         db.create_all()
with app.app_context():
    db.create_all()
# Register blueprints
app.register_blueprint(email_bp)
app.register_blueprint(github_bp)
app.register_blueprint(user_bp)
app.register_blueprint(email_pass_reset_bp)
app.register_blueprint(memory_chatbot_blueprint)
# Run the app
if __name__ == "__main__":
    app.run(debug=app.config["ENV"] == "development")
