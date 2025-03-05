from authlib.integrations.flask_client import OAuth
from Properties.authproperties import *

oauth = OAuth()
# Register GitHub OAuth client (oauth is initialized in app.py)
github = oauth.register(
    name="github",
    client_id=github_cliend_id,
    client_secret=github_client_secret,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


# # Initialize OAuth
# def init_oauth(app):
#     oauth = OAuth(app)
#     return oauth
