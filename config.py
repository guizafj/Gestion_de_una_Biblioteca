import os
from dotenv import load_dotenv
import logging

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

class Config:
    """
    Configuración principal de la aplicación Flask.
    """

    # Configuración de la base de datos
    SECRET_KEY = os.getenv('SECRET_KEY', 'defaultsecretkey')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
    )
    # Desactiva el seguimiento de modificaciones para mejorar el rendimiento
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('FLASK_ENV') == 'development' 

    # Clave secreta para la aplicación
    SECRET_KEY = os.getenv('SECRET_KEY', 'defaultsecretkey')
    if not SECRET_KEY:
        raise ValueError("La variable SECRET_KEY no está configurada.")
    
    SERVER_NAME = '127.0.0.1:5000'  # Reemplaza con tu dominio o dirección IP

    # Configuración de Flask-Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # Modo debug (solo para desarrollo)
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']

    # Configuración de cookies seguras
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() in ['true', '1', 't']
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() in ['true', '1', 't']
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

    # Preferencia de esquema de URL (http o https)
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'http')


    # Configuración del logging
    logging.basicConfig(filename='app.log', level=logging.INFO)
