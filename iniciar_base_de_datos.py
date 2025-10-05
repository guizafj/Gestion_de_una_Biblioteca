"""
Script para inicializar la base de datos de la aplicación de biblioteca.

Este script crea todas las tablas definidas en los modelos de SQLAlchemy.
Se recomienda ejecutarlo antes de iniciar la aplicación por primera vez
o al preparar un entorno de pruebas.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from main import create_app
from extensions import db
import logging

# Configurar logging para registrar eventos importantes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """
    Inicializa la base de datos de la aplicación.

    - Crea la aplicación Flask en modo testing.
    - Crea todas las tablas definidas en los modelos.
    - Registra el resultado en el log.

    Raises:
        Exception: Si ocurre un error durante la inicialización.
    """
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
