from flask import Flask, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from extensions import db, mail
from modules.auth import load_user
from modules.models_prestamo import Prestamo
from modules.models_libro import Libro
from modules.models_usuario import Usuario
from werkzeug.middleware.proxy_fix import ProxyFix
import urllib.parse
import logging
import os
from modules.routes_generales import generales_bp
from modules.routes_auth import auth_bp
from modules.routes_usuarios import usuarios_bp
from modules.routes_libros import libros_bp
from modules.routes_prestamos import prestamos_bp


def create_app(testing=False):
    """
    Crea y configura la aplicación Flask.
    Args:
        testing (bool): Si es True, usa configuración para pruebas.
    """
    app = Flask(__name__)
    if testing:
        app.config.from_object('tests.config_test.TestConfig')
    else:
        app.config.from_object(Config)

    # Configuración del logging
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Validar configuraciones críticas
    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY no está configurado.")
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise ValueError("SQLALCHEMY_DATABASE_URI no está configurado.")

    # Configuración base de URLs
    if not testing:
        app.config['PREFERRED_URL_SCHEME'] = 'http'
        app.config['APPLICATION_ROOT'] = '/'
        app.wsgi_app = ProxyFix(app.wsgi_app)

    # Inicializar extensiones
    initialize_extensions(app)

    # Registrar Blueprints
    app.register_blueprint(generales_bp)  # Rutas generales (errores, favicon, etc.)
    app.register_blueprint(auth_bp, url_prefix='/auth')  # Rutas de autenticación
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')  # Rutas de usuarios
    app.register_blueprint(libros_bp, url_prefix='/libros')  # Rutas de libros
    app.register_blueprint(prestamos_bp, url_prefix='/prestamos')  # Rutas de préstamos

    # Añadir filtro personalizado para decodificar URLs
    @app.template_filter('unquote_url')
    def unquote_url_filter(url):
        return urllib.parse.unquote(url)

    # Añadir función auxiliar para URLs limpias
    @app.context_processor
    def utility_processor():
        def get_clean_url(endpoint, **kwargs):
            url = url_for(endpoint, **kwargs)
            return urllib.parse.unquote(url)
        return dict(get_clean_url=get_clean_url)

    return app


def initialize_extensions(app):
    """
    Inicializa las extensiones de Flask.
    """
    db.init_app(app)
    mail.init_app(app)

    migrate = Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.user_loader(load_user)

    # Deshabilitar strict_slashes
    app.url_map.strict_slashes = False


# Crear la aplicación en el nivel superior
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    with app.app_context():
        try:
            db.engine.execute('SELECT 1')
            print("Conexión a la base de datos exitosa.")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")