from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message, Mail

mail = Mail()


secret_key = "default_secret_key"
s = URLSafeTimedSerializer(secret_key)


# Now you can call create_serializer() wherever you need the serializer
