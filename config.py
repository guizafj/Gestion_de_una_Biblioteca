import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///biblioteca.db') # Usamos SQLite para desarrollo
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Desactivamos el seguimiento de modificaciones

    # Clave secreta para proteger las sesiones y los formularios
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_por_defecto')  # Cambia esto por una clave segura en producción

    # Configuración de Flask-Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'mail.ecolibri.art')  # Cambia esto según tu proveedor de correo
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))  # Convertimos a entero
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'  # Convertimos a booleano
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'  # Convertimos a booleano
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'correo_por_defecto@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'contraseña_por_defecto')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@ecolibri.art')

    # Modo debug para desarrollo
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'  # Convertimos a booleano