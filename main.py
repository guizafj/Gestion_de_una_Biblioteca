"""
Archivo principal de la aplicación Flask para la gestión de biblioteca.

Este módulo:
- Crea y configura la aplicación Flask.
- Inicializa extensiones como SQLAlchemy, Flask-Mail, Flask-Migrate y Flask-Login.
- Registra los Blueprints de rutas principales.
- Añade filtros y utilidades para plantillas.
- Valida configuraciones críticas antes de iniciar la app.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from flask import Flask, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix  # Importar ProxyFix
from config import Config
from extensions import db, mail
from src.auth import load_user
from src.models import models_usuario
import logging
from src.routes.routes_generales import generales_bp
from src.routes.routes_auth import auth_bp
from src.routes.routes_usuarios import usuarios_bp
from src.routes.routes_libros import libros_bp
from src.routes.routes_prestamos import prestamos_bp
import urllib.parse


def create_app(testing=False):
    """
    Crea y configura la aplicación Flask.

    Args:
        testing (bool): Si es True, usa configuración para pruebas.

    Returns:
        Flask: Instancia de la aplicación Flask configurada.
    """
    app = Flask(__name__)
    if testing:
        app.config.from_object("tests.config_test.TestConfig")
    else:
        app.config.from_object(Config)

    # Configuración del logging
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Validar configuraciones críticas
    if not app.config.get("SECRET_KEY"):
        raise ValueError("SECRET_KEY no está configurado.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise ValueError("SQLALCHEMY_DATABASE_URI no está configurado.")

    # Configuración base de URLs y proxy (para despliegue detrás de proxy inverso)
    if not testing:
        app.config["PREFERRED_URL_SCHEME"] = "http"
        app.config["APPLICATION_ROOT"] = "/"
        app.wsgi_app = ProxyFix(app.wsgi_app)

    # Inicializar extensiones (DB, Mail, Migrate, LoginManager)
    initialize_extensions(app)

    # Registrar Blueprints para separar las rutas por funcionalidad
    app.register_blueprint(generales_bp)  # Rutas generales (errores, favicon, etc.)
    app.register_blueprint(auth_bp, url_prefix="/auth")  # Rutas de autenticación
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")  # Rutas de usuarios
    app.register_blueprint(libros_bp, url_prefix="/libros")  # Rutas de libros
    app.register_blueprint(prestamos_bp, url_prefix="/prestamos")  # Rutas de préstamos

    # Filtro personalizado para decodificar URLs en plantillas
    @app.template_filter("unquote_url")
    def unquote_url_filter(url):
        return urllib.parse.unquote(url)

    # Función auxiliar para obtener URLs limpias en plantillas
    @app.context_processor
    def utility_processor():
        def get_clean_url(endpoint, **kwargs):
            url = url_for(endpoint, **kwargs)
            return urllib.parse.unquote(url)

        return dict(get_clean_url=get_clean_url)

    return app


def initialize_extensions(app):
    """
    Inicializa las extensiones de Flask (DB, Mail, Migrate, LoginManager).

    Args:
        app (Flask): Instancia de la aplicación Flask.
    """
    db.init_app(app)
    mail.init_app(app)
    Migrate(app, db)  # Eliminamos la asignación a la variable `migrate`

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.user_loader(load_user)

    # Deshabilitar strict_slashes para mayor flexibilidad en rutas
    app.url_map.strict_slashes = False


# Crear la aplicación en el nivel superior para facilitar importación y pruebas
app = create_app()

if __name__ == "__main__":
    # Ejecutar la aplicación Flask en modo desarrollo
    app.run(host="0.0.0.0", port=5000, debug=True)
    # Probar la conexión a la base de datos al iniciar
    with app.app_context():
        try:
            db.engine.execute("SELECT 1")
            print("Conexión a la base de datos exitosa.")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
