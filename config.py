import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

class Config:
    """
    Configuración principal de la aplicación Flask.
    """

    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("La variable SQLALCHEMY_DATABASE_URI no está configurada.")
    # Asegurarse de que la base de datos use UTF-8 (para MySQL/MariaDB)
    if 'mysql' in SQLALCHEMY_DATABASE_URI and 'charset' not in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI += '?charset=utf8mb4'

    # Clave secreta para la aplicación
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("La variable SECRET_KEY no está configurada.")

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

    # Configuración de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Desactiva el seguimiento de modificaciones para mejorar el rendimiento