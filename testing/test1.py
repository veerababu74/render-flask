from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from datetime import timedelta
from flask_cors import cross_origin
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth
import bcrypt
import datetime
from flask_cors import CORS
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Enable CORS for frontend interactions
CORS(app, resources={r"/reset_password/*": {"origins": "http://localhost:3004"}})
# Configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SECRET_KEY"] = "your_secret_key"
app.config["JWT_SECRET_KEY"] = "jwt_secret_key"
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "pveerababu199966@gmail.com"  # Replace with your email
app.config["MAIL_PASSWORD"] = "fqxwfjhdlhalsdme"  # Replace with your email password
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["GITHUB_CLIENT_ID"] = (
    "Ov23li9DdvoPK2xLxf0B"  # Replace with your GitHub Client ID
)
app.config["GITHUB_CLIENT_SECRET"] = (
    "39b36e0fa4d51a5dff2e0b3fc93371d1fa039722"  # Replace with your GitHub Client Secret
)
app.config["GITHUB_REDIRECT_URI"] = "http://127.0.0.1:5000/authorize"

db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)
oauth = OAuth(app)

# GitHub OAuth Setup
github = oauth.register(
    name="github",
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    refresh_token_url=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

# URLSafeTimedSerializer for generating reset password tokens
s = URLSafeTimedSerializer(app.config["SECRET_KEY"])


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    oauth_provider = db.Column(
        db.String(50), nullable=True
    )  # To store OAuth provider name (e.g., GitHub)


# OAuth Table
class OAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(50), nullable=False)
    user = db.relationship("User", backref=db.backref("oauth", lazy=True))


# Initialize database (run once)
with app.app_context():
    db.create_all()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # Get username and password from the request
    username = data.get("username")
    password = data.get("password")

    # Find the user by username
    user = User.query.filter_by(username=username).first()

    # Check if user exists and if the password is correct
    if user and check_password_hash(
        user.password, password
    ):  # Ensure the password is hashed
        # Create JWT token (valid for 1 hour)
        access_token = create_access_token(
            identity=user.id, fresh=True, expires_delta=timedelta(hours=1)
        )

        return jsonify(access_token=access_token), 200

    return jsonify(message="Invalid credentials!"), 401


# register
# User Registration
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    # Check if user exists by username
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"message": "User already exists!"}), 400

    # Hash the password using pbkdf2:sha256
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

    # Add new user with hashed password
    new_user = User(username=username, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()

    # Generate verification token
    token = s.dumps(email, salt="email-verify")

    # Send verification email
    verification_link = url_for("verify_email", token=token, _external=True)
    send_verification_email(email, verification_link)

    return (
        jsonify(
            {
                "message": "User created successfully! Please check your email to verify your account."
            }
        ),
        201,
    )


def send_verification_email(email, verification_link):
    msg = Message(
        "Email Verification", sender="pveerababu199966@gmail.com", recipients=[email]
    )
    msg.body = f"Please click the link to verify your email: {verification_link}"
    mail.send(msg)


# Email Verification
@app.route("/verify_email/<token>", methods=["GET"])
@cross_origin(origins="http://localhost:3004")
def verify_email(token):
    try:
        email = s.loads(
            token, salt="email-verify", max_age=3600
        )  # Token expires after 1 hour
    except Exception as e:
        return (
            jsonify({"message": "The verification link is invalid or has expired."}),
            400,
        )

    # Mark user as verified
    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified:
        user.is_verified = True
        db.session.commit()
        return redirect(
            "http://127.0.0.1:5000//hello_world"
        )  # Redirect to frontend route
    return jsonify({"message": "User not found or already verified."}), 400


# Resend Verification Email
@app.route("/resend_verification_email", methods=["POST"])
@cross_origin(origins="http://localhost:3004")
def resend_verification_email():
    data = request.get_json()
    email = data.get("email")

    # Check if user exists and is not verified
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found!"}), 404
    if user.is_verified:
        return jsonify({"message": "User is already verified!"}), 400

    # Generate verification token
    token = s.dumps(email, salt="email-verify")

    # Send verification email
    verification_link = url_for("verify_email", token=token, _external=True)
    send_verification_email(email, verification_link)

    return (
        jsonify({"message": "A new verification link has been sent to your email."}),
        200,
    )


#


# Send password reset email
def send_password_reset_email(email, reset_link):
    msg = Message(
        "Password Reset Request", sender="your_email@gmail.com", recipients=[email]
    )
    msg.body = f"Click the following link to reset your password: {reset_link}"
    mail.send(msg)


# Request Password Reset
@app.route("/request_password_reset", methods=["POST", "OPTIONS"])
@cross_origin(origins="http://localhost:3004")
def request_password_reset():
    data = request.get_json()
    email = data.get("email")

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found!"}), 404

    # Generate password reset token
    token = s.dumps(email, salt="password-reset")

    # Send password reset email
    reset_link = url_for("reset_password_redirect", token=token, _external=True)
    send_password_reset_email(email, reset_link)

    return jsonify({"message": "Password reset link has been sent to your email."}), 200


# Redirect User to Frontend Page for Resetting Password
@app.route("/reset_password_redirect/<token>", methods=["POST", "OPTIONS"])
@cross_origin(origins="http://localhost:3004")
def reset_password_redirect(token):
    try:
        # Validate the token
        email = s.loads(
            token, salt="password-reset", max_age=3600
        )  # Token expires in 1 hour
    except Exception as e:
        return (
            jsonify({"message": "The password reset link is invalid or has expired."}),
            400,
        )

    # Redirect to frontend page where password can be reset
    frontend_reset_url = f"http://localhost:3004/reset_password/{token}"
    return redirect(frontend_reset_url)


# @app.route("/reset_password/<token>", methods=["POST"])
# def reset_password(token):
#     try:
#         # Validate the token
#         email = s.loads(token, salt="password-reset", max_age=3600)
#     except Exception as e:
#         return (
#             jsonify({"message": "The password reset link is invalid or has expired."}),
#             400,
#         )

#     # Get the new password from the request
#     data = request.get_json()
#     new_password = data.get("password")  # Ensure this field is in the request body

#     if not new_password:
#         return jsonify({"message": "Password is required!"}), 400

#     # Find the user by email and update the password
#     user = User.query.filter_by(email=email).first()
#     if not user:
#         return jsonify({"message": "User not found!"}), 404

#     # Hash the new password
#     hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
#     user.password = hashed_password
#     db.session.commit()

#     return jsonify({"message": "Password has been successfully reset!"}), 200


if __name__ == "__main__":
    app.run(debug=True)
