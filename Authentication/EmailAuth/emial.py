from flask import Blueprint, request, jsonify, current_app, url_for, redirect
from DataBase.Models.usermodels import db, User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from datetime import timedelta
from flask_cors import cross_origin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadData
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
from .mailAuth import mail, s


from Properties.urls import FRONTEND_BASE_URL_FOR_CORS, FRONTEND_BASE_URL

# Initialize bcrypt
bcrypt = Bcrypt()

# Define the Blueprint
email_bp = Blueprint(name="email_bp", import_name=__name__)


# Function to generate JWT token
def generate_jwt_token(user_id):
    """Function to generate JWT token."""
    access_token = create_access_token(
        identity=str(user_id), fresh=True, expires_delta=timedelta(hours=1)
    )
    return access_token


# Function to send verification email
def send_verification_email(email, verification_link):
    msg = Message(
        "Email Verification", sender="pveerababu199966@gmail.com", recipients=[email]
    )
    msg.body = f"Please click the link to verify your email: {verification_link}"
    mail.send(msg)


# Registration Route
@email_bp.route("/register", methods=["POST"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
# Allow CORS for your frontend
def register_email():
    """Endpoint to register a new user."""
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    firstname = data.get("firstname")
    lastname = data.get("lastname", "")

    # Check if any of the required fields are missing
    if (
        not username
        or not email
        or not password
        or not firstname
        or not confirm_password
    ):
        return jsonify({"error": "Missing fields"}), 400

    # Validate that password and confirm_password match
    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.email == email) | (User.username == username)
    ).first()
    if existing_user:
        return (
            jsonify({"error": "User with this email or username already exists"}),
            400,
        )

        # Validate password strength
    if not User.validate_password(password):
        return (
            jsonify(
                {
                    "error": "Password must be at least 6 characters long, contain a capital letter, and include a special symbol"
                }
            ),
            400,
        )

    # Hash the password before saving
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        firstname=firstname,
        lastname=lastname,
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        # Generate email verification token
        token = s.dumps(email, salt="email-verify")

        # Generate verification link
        verification_link = url_for(
            "email_bp.verify_email", token=token, _external=True
        )

        # Send verification email
        send_verification_email(email, verification_link)

        return (
            jsonify(
                {
                    "message": "User registered successfully. Please check your email to verify."
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# Route to verify email using the token
@email_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    """Endpoint to verify the user's email using the token."""
    try:
        email = s.loads(
            token, salt="email-verify", max_age=3600
        )  # Token expires after 1 hour
        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "Invalid token or user not found"}), 400

        user.is_verified = True
        db.session.commit()
        frontend_url = f"{FRONTEND_BASE_URL}/login"
        return redirect(f"{frontend_url}")
        # return jsonify({"message": "Email verified successfully!"}), 200

    except SignatureExpired:
        return jsonify({"error": "The verification link has expired"}), 400
    except BadSignature:
        return jsonify({"error": "Invalid verification token"}), 400


@email_bp.route("/resend_verification_email", methods=["POST"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
@jwt_required()  # Protect the route with JWT authentication
def resend_verification_email():
    current_user_id = get_jwt_identity()  # Get the current user's ID from the JWT
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found!"}), 404

    # If the user is already verified, return an appropriate response
    if user.is_verified:
        return jsonify({"message": "User is already verified!"}), 400

    # Generate verification token and send verification email
    token = s.dumps(user.email, salt="email-verify")
    verification_link = url_for("email_bp.verify_email", token=token, _external=True)
    send_verification_email(user.email, verification_link)

    return (
        jsonify({"message": "A new verification link has been sent to your email."}),
        200,
    )


@email_bp.route("/login", methods=["POST"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
def login_email():
    """Endpoint for user login."""
    data = request.get_json()
    identifier = data.get("identifier")  # This will be either email or username
    password = data.get("password")

    if not identifier or not password:
        return (
            jsonify({"error": "Missing identifier (email/username) or password"}),
            400,
        )

    # Search for the user by email or username
    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user:
        return jsonify({"error": "User does not exist"}), 404

    if bcrypt.check_password_hash(user.password, password):
        # Generate JWT token on successful login
        access_token = generate_jwt_token(user.id)
        is_verified = user.is_verified
        return (
            jsonify(
                {
                    "message": "Login successful",
                    "token": access_token,
                    "is_verified": is_verified,
                }
            ),
            200,
        )

    return jsonify({"error": "Invalid credentials"}), 401


# Example Protected Route (requires JWT authentication)
@email_bp.route("/veera")
@jwt_required()
def veera():
    return jsonify({"message": "Welcome to the Flask App! Your email is verified."})
