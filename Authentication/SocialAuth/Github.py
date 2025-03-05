# from flask import Blueprint, request, jsonify, redirect, url_for
# from authlib.integrations.flask_client import OAuth
# from flask_bcrypt import Bcrypt

# import jwt
# import datetime

# from DataBase.Models.usermodels import db, User
# from Properties.authproperties import github_cliend_id, github_client_secret

# # Initialize bcrypt and OAuth
# bcrypt = Bcrypt()
# oauth = OAuth()

# # Define the Blueprint for GitHub Auth
# github_bp = Blueprint(
#     name="github_bp",
#     import_name=__name__,
#     url_prefix="/githubauth",  # You can change this prefix if needed
# )

# # Register GitHub OAuth client
# github = oauth.register(
#     name="github",
#     client_id=github_cliend_id,
#     client_secret=github_client_secret,
#     access_token_url="https://github.com/login/oauth/access_token",
#     authorize_url="https://github.com/login/oauth/authorize",
#     api_base_url="https://api.github.com/",
#     client_kwargs={"scope": "user:email"},
# )


# @github_bp.route("/login/github", methods=["GET", "OPTIONS"])
# def login_with_github():
#     """Redirect user to GitHub for login"""
#     redirect_uri = url_for(
#         "github_bp.authorize", _external=True
#     )  # ensure correct route
#     return github.authorize_redirect(redirect_uri)


# @github_bp.route("/authorize")
# def authorize():
#     """Handle GitHub OAuth authorization"""
#     try:
#         token = github.authorize_access_token()  # Get the access token
#         user_info = github.get("user").json()  # Fetch user info from GitHub API

#         # Check if the user exists in the database
#         user = User.query.filter_by(github_id=user_info["id"]).first()
#         if not user:
#             user = User(username=user_info["login"], github_id=user_info["id"])
#             db.session.add(user)
#             db.session.commit()

#         # Generate a JWT token for the user
#         access_token = generate_jwt_token(user.id)

#         # Redirect the user to the frontend with the token and username
#         frontend_url = (
#             "http://localhost:3000/github-redirect"  # Change this to your frontend URL
#         )
#         return redirect(f"{frontend_url}?token={access_token}&username={user.username}")

#     except Exception as e:
#         return jsonify({"error": f"Authorization failed: {e}"}), 500


# def generate_jwt_token(user_id):
#     """Generate a JWT token for the authenticated user"""
#     expiration_time = datetime.datetime.utcnow() + datetime.timedelta(
#         hours=1
#     )  # Token expires in 1 hour
#     token = jwt.encode(
#         {"user_id": user_id, "exp": expiration_time},
#         "your_secret_key",  # Use your app's secret key here
#         algorithm="HS256",
#     )
#     return token


from flask import Blueprint, request, jsonify, redirect, url_for
from authlib.integrations.flask_client import OAuth
from flask_bcrypt import Bcrypt
from flask_cors import cross_origin
from DataBase.Models.usermodels import db, User, OAuthUser
from Properties.authproperties import github_cliend_id, github_client_secret
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from datetime import timedelta
from .Auth import github

from Properties.urls import FRONTEND_BASE_URL_FOR_CORS, FRONTEND_BASE_URL

# Initialize bcrypt
bcrypt = Bcrypt()

# GitHub OAuth Setup (don't initialize oauth here, it's done in app.py)
github_bp = Blueprint(
    name="github_bp",
    import_name=__name__,
)


def generate_jwt_token(user_id):
    """Function to generate JWT token."""
    # Using `create_access_token` to generate the JWT with a 1-hour expiration
    access_token = create_access_token(
        identity=str(user_id), fresh=True, expires_delta=timedelta(hours=1)
    )
    return access_token


@github_bp.route("/login/github", methods=["GET", "OPTIONS"])
##@cross_origin(origins=FRONTEND_BASE_URL_FOR_CORS, supports_credentials=True)


def login_with_github():
    """Redirect user to GitHub for login"""
    redirect_uri = url_for("github_bp.authorize", _external=True)
    return github.authorize_redirect(redirect_uri)


@github_bp.route("/authorize")
def authorize():
    """Handle GitHub OAuth authorization"""
    try:
        token = github.authorize_access_token()  # Get the access token
        user_info = github.get("user").json()  # Fetch user info from GitHub API

        # Check if the OAuth user already exists
        oauth_user = OAuthUser.query.filter_by(oauth_id=user_info["id"]).first()

        # If OAuth user doesn't exist, create a new user and link OAuth
        if not oauth_user:
            # Safely handle name and split it if available
            name = user_info.get("name", "")
            name_parts = name.split() if name else []

            # Set firstname and lastname based on the split name
            firstname = name_parts[0] if name_parts else ""
            lastname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            # Get email from GitHub (can be empty or None)
            email = user_info.get("email", "")
            if not email:
                email = f"{user_info['login']}@github.com"

            # Create a new user
            user = User(
                username=user_info["login"],
                firstname=firstname,
                lastname=lastname,
                email=email,
            )
            db.session.add(user)
            db.session.commit()

            # Link the new user to the OAuth provider
            oauth_user = OAuthUser(
                user_id=user.id, oauth_provider="github", oauth_id=user_info["id"]
            )
            db.session.add(oauth_user)
            db.session.commit()
        else:
            # Retrieve the linked User object
            user = oauth_user.user

        # Generate JWT token
        access_token = generate_jwt_token(user.id)

        # Redirect the user to the frontend with the token and username
        frontend_url = f"{FRONTEND_BASE_URL}/github-redirect"
        return redirect(f"{frontend_url}?token={access_token}&username={user.username}")

    except Exception as e:
        return jsonify({"error": f"Authorization failed: {e}"}), 500
