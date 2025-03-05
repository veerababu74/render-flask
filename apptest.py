from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth
import bcrypt
import datetime
from Properties.urls import FRONTEND_BASE_URL, AUTH_URLS, API_BASE_URL

app = Flask(__name__)

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
app.config["GITHUB_REDIRECT_URI"] = f"{API_BASE_URL}/authorize"

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


# Send Reset Password Email
def send_reset_email(user, reset_link):
    msg = Message(
        "Password Reset Request",
        sender="pveerababu199966@gmail.com",
        recipients=[user.email],
    )
    msg.body = f"Click the link to reset your password: {reset_link}"
    mail.send(msg)


# Request Password Reset
@app.route("/reset_password", methods=["POST"])
def reset_password_request():
    email = request.json.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "Email not found."}), 404

    # Generate reset token
    token = s.dumps(email, salt="password-reset")

    # Create reset password link
    reset_link = url_for("reset_password", token=token, _external=True)

    # Send the reset email
    send_reset_email(user, reset_link)

    return jsonify({"message": "Password reset email sent."}), 200


# Reset Password
@app.route("/reset_password/<token>", methods=["POST"])
def reset_password(token):
    try:
        # Verify token
        email = s.loads(
            token, salt="password-reset", max_age=3600
        )  # Token expires after 1 hour
    except Exception:
        return jsonify({"message": "The reset link is invalid or has expired."}), 400

    # Get new password from request
    new_password = request.json.get("password")

    # Find the user and update the password
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found."}), 404

    # Hash the new password
    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    # Update the password
    user.password = hashed_password.decode("utf-8")
    db.session.commit()

    return jsonify({"message": "Password has been successfully reset."}), 200


# User Registration
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    # Check if user exists
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"message": "User already exists!"}), 400

    # Add new user
    new_user = User(username=username, password=password, email=email)
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
        return redirect(AUTH_URLS["HELLO_WORLD"])
    return jsonify({"message": "User not found or already verified."}), 400


# Hello World route (for redirection after verification)
@app.route("/hello_world")
def hello_world():
    return "Hello, world! Your email has been verified."


# OAuth Login with GitHub
@app.route("/login/github")
def github_login():
    redirect_uri = url_for("github_callback", _external=True)
    return github.authorize_redirect(redirect_uri)


# OAuth Callback for GitHub
@app.route("/github_callback")
def github_callback():
    token = github.authorize_access_token()
    user_info = github.get("user")
    email_info = github.get("user/emails")

    email = None
    for e in email_info.json():
        if e["primary"] and e["verified"]:
            email = e["email"]
            break

    if not email:
        return jsonify({"message": "No verified email found for GitHub account."}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        # Create a new user linked to OAuth
        user = User(username=user_info.json()["login"], email=email, is_verified=True)
        db.session.add(user)
        db.session.commit()

    # Link OAuth data to user
    oauth_data = OAuth(
        user_id=user.id, provider="github", provider_user_id=user_info.json()["id"]
    )
    db.session.add(oauth_data)
    db.session.commit()

    return redirect(AUTH_URLS["GITHUB_CALLBACK"])  # Redirect to frontend route


# User Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return jsonify({"message": "Invalid credentials"}), 401

    # Check if user is verified
    if not user.is_verified:
        return (
            jsonify({"message": "Email not verified. Please verify your email."}),
            401,
        )

    # Create JWT token
    access_token = create_access_token(
        identity=username, expires_delta=datetime.timedelta(hours=1)
    )
    return jsonify(access_token=access_token), 200


if __name__ == "__main__":
    app.run(debug=True)
