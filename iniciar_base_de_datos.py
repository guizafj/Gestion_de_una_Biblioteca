from main import create_app
from extensions import db
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Inicializa la base de datos"""
    try:
        app = create_app(testing=True)  # Usar configuración de prueba
        with app.app_context():
            db.create_all()
            logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise

if __name__ == "__main__":
    init_db()


