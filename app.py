from flask import Flask  # Importamos Flask para crear la aplicación
# from flask_sqlalchemy import SQLAlchemy  # Para trabajar con la base de datos
from flask_login import LoginManager  # Manejo de sesiones de usuario
# from flask_mail import Mail  # Para enviar correos electrónicos

# Importamos las configuraciones centralizadas
from config import Config  # Configuraciones desde config.py
from extensions import db, mail  # Instancias compartidas de SQLAlchemy y Flask-Mail
from modules.auth import load_user  # Cargador de usuarios para Flask-Login

# Importaciones explícitas de rutas
from modules.routes import (
    index, agregar_libro, editar_libro, eliminar_libro, login, registro
)

def create_app():
    """
    Función factory para crear y configurar la aplicación Flask.
    Esto permite una mayor modularidad y facilidad para pruebas.
    """
    app = Flask(__name__)

    # Cargamos las configuraciones desde el archivo `config.py`
    app.config.from_object(Config)

    # Inicializamos las extensiones
    initialize_extensions(app)

    # Registramos las rutas
    register_routes(app)

    return app


def initialize_extensions(app):
    """
    Inicializa todas las extensiones de Flask.
    """
    db.init_app(app)  # Inicializamos SQLAlchemy
    mail.init_app(app)  # Inicializamos Flask-Mail para el envío de correos

    # Configuración de Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'  # Especificamos la ruta de inicio de sesión
    login_manager.user_loader(load_user)  # Asociamos el cargador de usuarios


def register_routes(app):
    """
    Registra todas las rutas de la aplicación.
    """
    app.add_url_rule('/', 'index', index)
    app.add_url_rule('/agregar_libro', 'agregar_libro', agregar_libro, methods=['GET', 'POST'])
    app.add_url_rule('/editar_libro/<int:id>', 'editar_libro', editar_libro, methods=['GET', 'POST'])
    app.add_url_rule('/eliminar_libro/<int:id>', 'eliminar_libro', eliminar_libro, methods=['POST'])
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/registro', 'registro', registro, methods=['GET', 'POST'])


# Si ejecutamos este archivo directamente, iniciamos la aplicación
if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'])  # El modo debug se controla desde `config.py`