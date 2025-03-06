import os


class BaseConfig:
    """Base configuration shared across environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Mail Configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "pveerababu199966@gmail.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "fqxwfjhdlhalsdme")
    MAIL_DEFAULT_SENDER = MAIL_USERNAME


class DevelopmentConfig(BaseConfig):
    """Configuration for development environment."""

    ENV = "development"
    DEBUG = True

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, "DataBase", "instance")
    os.makedirs(DATABASE_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(DATABASE_DIR, 'database.sqlite')}"
    )


class ProductionConfig(BaseConfig):
    """Configuration for production environment."""

    ENV = "production"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://username:password@localhost/production_db"
    )


def configure_app(app):
    """Apply the appropriate configuration based on the environment."""
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)


# import os


# class BaseConfig:
#     SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")
#     JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     JWT_TOKEN_LOCATION = ["headers"]
#     JWT_HEADER_NAME = "Authorization"
#     JWT_HEADER_TYPE = "Bearer"

#     MAIL_SERVER = "smtp.gmail.com"
#     MAIL_PORT = 587
#     MAIL_USE_TLS = True
#     MAIL_USE_SSL = False
#     MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "pveerababu199966@gmail.com")
#     MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "fqxwfjhdlhalsdme")
#     MAIL_DEFAULT_SENDER = MAIL_USERNAME

#     CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")


# class DevelopmentConfig(BaseConfig):
#     ENV = "development"
#     DEBUG = True

#     BASE_DIR = os.path.abspath(os.path.dirname(__file__))
#     DATABASE_DIR = os.path.join(BASE_DIR, "DataBase", "instance")
#     os.makedirs(DATABASE_DIR, exist_ok=True)
#     SQLALCHEMY_DATABASE_URI = (
#         f"sqlite:///{os.path.join(DATABASE_DIR, 'database.sqlite')}"
#     )


# class ProductionConfig(BaseConfig):
#     ENV = "production"
#     DEBUG = False
#     SQLALCHEMY_DATABASE_URI = os.environ.get(
#         "DATABASE_URL", "mysql+pymysql://username:password@localhost/production_db"
#     )
