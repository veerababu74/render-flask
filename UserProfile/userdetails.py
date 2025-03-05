from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from DataBase.Models.database import db
from DataBase.Models.usermodels import User
import jwt
from datetime import datetime, timedelta
from flask_cors import cross_origin
from Properties.urls import FRONTEND_BASE_URL_FOR_CORS

# Initialize Flask extensions
bcrypt = Bcrypt()
mail = Mail()

user_bp = Blueprint("user_bp", __name__)


# Helper function to create email verification token
def create_email_verification_token(user_id, new_email, secret_key):
    payload = {
        "user_id": user_id,
        "new_email": new_email,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


# # Helper function to send verification email
# def send_email_verification(new_email, token, mail_server):
#     verification_link = f"http://localhost:5000/user/verify-email?token={token}"
#     msg = Message(
#         subject="Email Verification", sender=mail_server, recipients=[new_email]
#     )
#     msg.body = f"Please verify your new email address by clicking on this link: {verification_link}"
#     mail.send(msg)


# @user_bp.route("/update-user", methods=["PUT"])
# @jwt_required()
# def update_user_details():
#     try:
#         user_id = get_jwt_identity()
#         user = User.query.get(user_id)
#         if not user:
#             return jsonify({"error": "User not found"}), 404

#         data = request.json
#         if not data:
#             return jsonify({"error": "No data provided"}), 400

#         # Debugging: Log the incoming data
#         print("Received data:", data)

#         user.firstname = data.get("firstname", user.firstname)
#         user.lastname = data.get("lastname", user.lastname)

#         new_email = data.get("email")
#         if new_email and new_email != user.email:
#             # Check if the new email is already in use
#             if User.query.filter(User.email == new_email, User.id != user.id).first():
#                 return jsonify({"error": "Email is already in use"}), 400

#             # Generate confirmation token and send email
#             confirmation_token = create_email_verification_token(
#                 user_id, new_email, user_bp.app.config["JWT_SECRET_KEY"]
#             )
#             send_email_verification(
#                 new_email, confirmation_token, user_bp.app.config["MAIL_USERNAME"]
#             )

#             return (
#                 jsonify(
#                     {
#                         "message": "Email update initiated. Please verify your new email address."
#                     }
#                 ),
#                 200,
#             )

#         # Handle password change
#         new_password = data.get("password")
#         if new_password:
#             user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")

#         db.session.commit()

#         updated_user = {
#             "id": user.id,
#             "username": user.username,
#             "firstname": user.firstname,
#             "lastname": user.lastname,
#             "email": user.email,
#         }
#         return (
#             jsonify(
#                 {"message": "User details updated successfully", "user": updated_user}
#             ),
#             200,
#         )

#     except Exception as e:
#         # Log the exception to get more details
#         print("Error:", str(e))
#         return jsonify({"error": f"Failed to update user details: {str(e)}"}), 500


# Update Profile Route
@user_bp.route("/update_profile", methods=["PUT"])
@jwt_required()
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
def update_profile():
    """Endpoint to update user profile (password, firstname, lastname)."""
    data = request.get_json()

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found!"}), 404

    new_firstname = data.get("firstname", user.firstname)
    new_lastname = data.get("lastname", user.lastname)
    new_password = data.get("password")
    old_password = data.get("old_password")

    if new_password:
        if not old_password:
            return (
                jsonify({"message": "Old password is required to change the password"}),
                400,
            )

        if not bcrypt.check_password_hash(user.password, old_password):
            return jsonify({"message": "Incorrect old password"}), 400

        if not User.validate_password(new_password):
            return (
                jsonify(
                    {
                        "error": "Password must be at least 6 characters long, contain a capital letter, and include a special symbol"
                    }
                ),
                400,
            )

        new_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        user.password = new_password

    user.firstname = new_firstname
    user.lastname = new_lastname

    try:
        db.session.commit()
        return jsonify({"message": "User profile updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "message": "An error occurred while updating the profile",
                    "error": str(e),
                }
            ),
            500,
        )


# User Details Route
@user_bp.route("/user_details", methods=["GET"])
@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)
@jwt_required()
def user_details():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found!"}), 404
    print(user)
    return (
        jsonify(
            {
                "username": user.username,
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "is_verified": user.is_verified,
            }
        ),
        200,
    )
