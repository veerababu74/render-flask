import os

DEV_ENVIRONMENT = "LOCAL"

FRONTEND_BASE_URL_FOR_CORS = "http://localhost:3000"
FRONTEND_BASE_URL_LOCAL = "http://localhost:3000"
FRONTEND_BASE_URL_PRODUCTION = "https://your-frontend-url.com"

FRONTEND_BASE_URL = (
    FRONTEND_BASE_URL_PRODUCTION
    if DEV_ENVIRONMENT == "production"
    else FRONTEND_BASE_URL_LOCAL
)

API_BASE_URL = "http://localhost:5000"

# Authentication URLs
AUTH_URLS = {
    "LOGIN_REDIRECT": f"{FRONTEND_BASE_URL}/login",
    "EMAIL_VERIFICATION_SUCCESS": f"{FRONTEND_BASE_URL}/verify-success",
    "PASSWORD_RESET": f"{FRONTEND_BASE_URL}/reset-password",
    "GITHUB_CALLBACK": f"{FRONTEND_BASE_URL}/auth/github/callback",
    "HELLO_WORLD": f"{FRONTEND_BASE_URL}/hello-world",
}
