from flask import Flask  # Importamos Flask para crear la aplicación
from flask_sqlalchemy import SQLAlchemy  # Importamos SQLAlchemy para trabajar con la base de datos
from flask_wtf.csrf import CSRFProtect  # Protección contra ataques CSRF
from flask_login import LoginManager  # Manejo de sesiones de usuario
from flask_mail import Mail, Message 

# Creamos la instancia de la aplicación Flask
app = Flask(__name__)

# Configuramos una clave secreta para proteger las sesiones y los formularios
app.config['SECRET_KEY'] = 'clave_secreta'  # Cambia esto por una clave segura en producción

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Cambia esto según tu proveedor de correo
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tu_correo@gmail.com'  # Tu correo electrónico
app.config['MAIL_PASSWORD'] = 'tu_contraseña'  # Tu contraseña de correo
app.config['MAIL_DEFAULT_SENDER'] = 'tu_correo@gmail.com'

mail = Mail(app)  # Inicializamos Flask-Mail

# Configuramos la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblioteca.db'  # Usamos SQLite para desarrollo
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desactivamos el seguimiento de modificaciones para mejorar el rendimiento

# Inicializamos las extensiones
db = SQLAlchemy(app)  # Inicializamos SQLAlchemy para manejar la base de datos
csrf = CSRFProtect(app)  # Activamos la protección CSRF
login_manager = LoginManager(app)  # Inicializamos Flask-Login para manejar la autenticación
login_manager.login_view = 'login'  # Especificamos la ruta de inicio de sesión

# Importamos los módulos al final para evitar problemas de importación circular
from modules.models import db  # Modelo de la base de datos
from modules.auth import load_user  # Cargador de usuarios para Flask-Login
from modules.routes import *  # Importamos todas las rutas

# Si ejecutamos este archivo directamente, iniciamos la aplicación
if __name__ == '__main__':
    app.run(debug=True)  # Modo debug activado para desarrollo