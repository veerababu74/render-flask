# from flask import Blueprint, request, jsonify, url_for, redirect, current_app
# from DataBase.Models.usermodels import db, User
# from flask_bcrypt import Bcrypt
# from flask_cors import cross_origin
# from itsdangerous import URLSafeTimedSerializer
# from flask_mail import Message
# from .mailAuth import mail, s

# # Define the Blueprint
# email_pass_reste_bp = Blueprint("email_pass_reste_bp", __name__)

# # Initialize bcrypt
# bcrypt = Bcrypt()


# # Helper function to send email
# def send_password_reset_email(email, reset_link):
#     try:
#         msg = Message(
#             "Password Reset Request", sender="your_email@gmail.com", recipients=[email]
#         )
#         msg.body = f"Click the following link to reset your password: {reset_link}"
#         mail.send(msg)
#     except Exception as e:
#         current_app.logger.error(f"Error sending email: {str(e)}")
#         raise


# # Request Password Reset
# @email_pass_reste_bp.route("/request_password_reset", methods=["POST", "OPTIONS"])
# #@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)


# def request_password_reset():
#     data = request.get_json()
#     if not data or "email" not in data:
#         return jsonify({"message": "Invalid request payload"}), 400

#     email = data.get("email")
#     user = User.query.filter_by(email=email).first()
#     if not user:
#         return jsonify({"message": "User not found!"}), 404

#     try:
#         token = s.dumps(email, salt="password-reset")
#         reset_link = (
#             f"http://localhost:3004/reset_password/{token}"  # Update link for React app
#         )
#         send_password_reset_email(email, reset_link)
#         return (
#             jsonify({"message": "Password reset link has been sent to your email."}),
#             200,
#         )
#     except Exception as e:
#         current_app.logger.error(f"Error generating reset link: {str(e)}")
#         return (
#             jsonify({"message": "An error occurred while processing your request."}),
#             500,
#         )


# # Reset Password API
# @email_pass_reste_bp.route("/reset_password/<token>", methods=["POST"])
# #@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)


# def reset_password(token):
#     try:
#         # Validate the token
#         email = s.loads(token, salt="password-reset", max_age=3600)
#     except Exception as e:
#         current_app.logger.error(f"Error validating token: {str(e)}")
#         return (
#             jsonify({"message": "The password reset link is invalid or has expired."}),
#             400,
#         )

#     # Get the new password from the request
#     data = request.get_json()
#     if not data:
#         return jsonify({"message": "Invalid request payload"}), 400

#     new_password = data.get("password")
#     confirm_password = data.get("confirm_password")

#     if not new_password or not confirm_password:
#         return jsonify({"message": "Both password fields are required."}), 400
#     if new_password != confirm_password:
#         return jsonify({"message": "Passwords do not match."}), 400

#     # Hash the new password
#     hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

#     # Update the user's password in the database
#     user = User.query.filter_by(email=email).first()
#     if not user:
#         return jsonify({"message": "User not found!"}), 404

#     user.password = hashed_password
#     db.session.commit()

#     return jsonify({"message": "Password has been reset successfully."}), 200
from flask import Blueprint, request, jsonify, current_app
from DataBase.Models.usermodels import db, User, PasswordResetToken
from flask_bcrypt import Bcrypt
from flask_cors import cross_origin
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from .mailAuth import mail


from Properties.urls import FRONTEND_BASE_URL_FOR_CORS, FRONTEND_BASE_URL

# Define the Blueprint
email_pass_reset_bp = Blueprint("email_pass_reset_bp", __name__)

# Initialize bcrypt
bcrypt = Bcrypt()

# Serializer for token generation
s = URLSafeTimedSerializer("your-secret-key")


# Helper function to send email
def send_password_reset_email(email, reset_link):
    try:
        msg = Message(
            "Password Reset Request", sender="your_email@gmail.com", recipients=[email]
        )
        msg.body = f"Click the following link to reset your password: {reset_link}"
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        raise


# Request Password Reset
@email_pass_reset_bp.route("/request_password_reset", methods=["POST", "OPTIONS"])
# @cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)


def request_password_reset():
    data = request.get_json()
    if not data or "email" not in data:
        return jsonify({"message": "Invalid request payload"}), 400

    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found!"}), 404

    try:
        # Generate a reset token
        token = s.dumps(email, salt="password-reset")
        # reset_link = (
        #     f"http://localhost:3004/reset_password/{token}"  # Update link for React app
        # )
        reset_link = (
            f"{FRONTEND_BASE_URL}/reset_password/{token}"  # Update link for React app
        )

        # Save the token in the database
        reset_token = PasswordResetToken(user_id=user.id, token=token)
        db.session.add(reset_token)
        db.session.commit()

        # Send the reset link
        send_password_reset_email(email, reset_link)
        return (
            jsonify({"message": "Password reset link has been sent to your email."}),
            200,
        )
    except Exception as e:
        current_app.logger.error(f"Error generating reset link: {str(e)}")
        return (
            jsonify({"message": "An error occurred while processing your request."}),
            500,
        )


# Reset Password API
@email_pass_reset_bp.route("/reset_password/<token>", methods=["POST"])
# @cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)


def reset_password(token):
    try:
        # Validate the token
        email = s.loads(token, salt="password-reset", max_age=3600)
        reset_token = PasswordResetToken.query.filter_by(
            token=token, used=False
        ).first()

        if not reset_token:
            return (
                jsonify(
                    {"message": "The password reset link is invalid or already used."}
                ),
                400,
            )
    except Exception as e:
        current_app.logger.error(f"Error validating token: {str(e)}")
        return (
            jsonify({"message": "The password reset link is invalid or has expired."}),
            400,
        )

    # Get the new password from the request
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid request payload"}), 400

    new_password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not new_password or not confirm_password:
        return jsonify({"message": "Both password fields are required."}), 400
    if new_password != confirm_password:
        return jsonify({"message": "Passwords do not match."}), 400
    if not User.validate_password(new_password):
        return (
            jsonify({"message": "Password does not meet complexity requirements."}),
            400,
        )

    # Hash the new password
    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

    # Update the user's password in the database
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found!"}), 404

    user.password = hashed_password
    db.session.commit()

    # Mark the reset token as used
    reset_token.used = True
    db.session.commit()

    return jsonify({"message": "Password has been reset successfully."}), 200
