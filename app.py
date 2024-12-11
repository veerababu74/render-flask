from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
import datetime
from dotenv import load_dotenv
import os
from flask import Flask

# Load environment variables from .env file
load_dotenv()
# Initialize app and configurations
app = Flask(__name__)

CORS(
    app,
)

# # CORS(app, supports_credentials=True)
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# # Set secret keys
# app.config["SECRET_KEY"] = "default_secret_key"  # For session cookies
# app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"  # For JWT signing
# JWT_SECRET = "jwt_secret_key"
# # GitHub OAuth configuration
# app.config["GITHUB_CLIENT_ID"] = "Ov23li9DdvoPK2xLxf0B"
# app.config["GITHUB_CLIENT_SECRET"] = "39b36e0fa4d51a5dff2e0b3fc93371d1fa039722"

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_jwt_secret_key")
app.config["GITHUB_CLIENT_ID"] = os.getenv("GITHUB_CLIENT_ID")
app.config["GITHUB_CLIENT_SECRET"] = os.getenv("GITHUB_CLIENT_SECRET")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")


# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
oauth = OAuth(app)

# Register GitHub OAuth
github = oauth.register(
    name="github",
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=True)
    github_id = db.Column(db.String(120), unique=True, nullable=True)


# Helper functions
def generate_jwt_token(user_id):
    return create_access_token(identity=str(user_id))


def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)
    
@app.route("/hello", methods=["GET", "OPTIONS"])
def helloworld():
    return {"hello": "world"}

# Routes
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username, email, password = (
        data.get("username"),
        data.get("email"),
        data.get("password"),
    )

    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(username=username, email=email, password=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except:
        return jsonify({"error": "User with this email already exists"}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = generate_jwt_token(user.id)
        return (
            jsonify({"message": "Login successful", "token": access_token}),
            200,
        )

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/login/github", methods=["GET", "OPTIONS"])
def login_with_github():
    redirect_uri = url_for("authorize", _external=True)
    return github.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    try:
        token = github.authorize_access_token()
        user_info = github.get("user").json()

        # Check if the user exists in the database
        user = User.query.filter_by(github_id=user_info["id"]).first()
        if not user:
            user = User(username=user_info["login"], github_id=user_info["id"])
            db.session.add(user)
            db.session.commit()

        # Generate a JWT token for the user
        access_token = generate_jwt_token(user.id)

        # Redirect the user to the frontend with the token and username as query params
        frontend_url = "https://reactfronend.onrender.com/github-redirect"  # Replace with your actual frontend URL

        return redirect(f"{frontend_url}?token={access_token}&username={user.username}")

    except Exception as e:
        return jsonify({"error": f"Authorization failed: {e}"}), 500


from flask import current_app, make_response
from datetime import datetime, timedelta


# @app.route("/authorize", methods=["GET", "OPTIONS"])
# def authorize():
#     token = github.authorize_access_token()  # This will fetch the token
#     user_info = github.get("user").json()  # Fetch user info from GitHub

#     # Simulate user login or creation logic (store info in your database)
#     user = {
#         "github_id": user_info["id"],
#         "username": user_info["login"],
#         "email": user_info.get("email", "N/A"),
#     }
#     # Generate JWT or session token
#     # Example: Generate a JWT token
#     access_token = create_access_token(identity=user["github_id"])

#     # Set the token as a cookie or store in session
#     response = redirect(
#         "http://localhost:3004/login"
#     )  # Redirect to frontend /get_cookie
#     # response = redirect("/get_cookie")
#     # response.set_cookie("access_token", access_token)
#     response.set_cookie(
#         "access_token",
#         access_token,
#         httponly=True,  # Prevent JavaScript access
#         secure=False,  # Set to True when using HTTPS in production
#         samesite="None",  # Allow cookies to be sent cross-origin
#     )

#     return response


@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"username": user.username, "email": user.email}), 200


@app.route("/update-profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    username, password = data.get("username"), data.get("password")

    if username:
        user.username = username
    if password:
        user.password = bcrypt.generate_password_hash(password).decode("utf-8")

    db.session.commit()
    return jsonify({"message": "Profile updated successfully"}), 200


@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "User logged out successfully"}), 200


@app.route("/data", methods=["POST"])
@jwt_required()
def handle_data():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    input_data = data.get("input_data")
    if not input_data:
        return jsonify({"error": "Missing 'input_data' field"}), 400

    return jsonify({"message": f"Hello, {user.username}! You sent: {input_data}"}), 200


SECRET_KEY = "veera"


@app.route("/api/user")
@jwt_required()
def get_user_data():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(
        {"username": current_user.username, "github_id": current_user.github_id}
    )


@app.route("/get_cookie")
def get_cookie():
    github_user = request.cookies.get("access_token")
    if github_user:
        return f"GitHub user from cookie: {github_user}"
    else:
        return "No GitHub user cookie found."


@app.before_request
def before_request():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if request.method.lower() == "options":
        return jsonify(headers), 200


@app.after_request
def set_csp(response):
    response.headers["Content-Security-Policy"] = "script-src 'self' 'unsafe-eval'"
    return response


@app.route("/me", methods=["GET"])
@jwt_required()
def get_user():
    user = get_current_user()
    if user:
        return jsonify({"username": user.username, "email": user.email})
    return jsonify({"error": "User not found"}), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
