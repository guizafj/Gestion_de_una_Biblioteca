from flask import Flask
from flask_login import LoginManager
from config import Config
from extensions import db, mail
from modules.auth import load_user
from modules.routes import register_routes  # Importamos register_routes

def create_app():
    """
    Crea y configura la aplicación Flask.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    initialize_extensions(app)

    # Registrar rutas
    register_routes(app, db, mail)

    return app

def initialize_extensions(app):
    """
    Inicializa las extensiones de Flask.
    """
    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.user_loader(load_user)

# Si ejecutamos este archivo directamente, iniciamos la aplicación
if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'])  # El modo debug se controla desde `config.py`