from flask import Flask, url_for
from flask_login import LoginManager
from config import Config
from extensions import db, mail
from modules.auth import load_user
from modules.routes import register_routes
from werkzeug.middleware.proxy_fix import ProxyFix
import urllib.parse
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

def create_app(testing=False):
    """
    Crea y configura la aplicación Flask.
    Args:
        testing (bool): Si es True, usa configuración para pruebas
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuración base de URLs
    if not testing:
        app.config['PREFERRED_URL_SCHEME'] = 'http'
        app.config['APPLICATION_ROOT'] = '/'
        app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Inicializar extensiones
    initialize_extensions(app)
    
    # Registrar rutas
    register_routes(app, db, mail)
    
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

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.user_loader(load_user)
    
    # Deshabilitar strict_slashes
    app.url_map.strict_slashes = False

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)