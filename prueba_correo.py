from flask import Flask
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv


app = Flask(__name__)
# Configuración de Flask-Mail
MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').lower() in ['true', '1', 't']
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)


with app.app_context():
    msg = Message(
        subject="Prueba de correo",
        recipients=["javierdiaz.1904@gmail.com"],
        body="Este es un correo de prueba."
    )
    mail.send(msg)
    print("Correo enviado exitosamente.")