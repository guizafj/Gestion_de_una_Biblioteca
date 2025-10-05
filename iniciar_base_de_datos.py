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


def init_db(testing=False):
    """
    Inicializa la base de datos de la aplicación.

    Args:
        testing (bool): Si es True, usa configuración de prueba. 
                    Si es False, usa configuración de producción con MariaDB.

    - Crea la aplicación Flask con la configuración especificada.
    - Verifica la conexión a la base de datos.
    - Crea todas las tablas definidas en los modelos.
    - Registra el resultado en el log.

    Raises:
        Exception: Si ocurre un error durante la inicialización.
    """
    try:
        app = create_app(testing=testing)
        with app.app_context():
            # Verificar conexión a la base de datos
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"✅ Conexión exitosa a: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Crear todas las tablas
            db.create_all()
            logger.info("✅ Base de datos inicializada correctamente - Todas las tablas creadas")
            
            # Mostrar tablas creadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"📋 Tablas disponibles: {', '.join(tables) if tables else 'Ninguna'}")
            
    except Exception as e:
        logger.error(f"❌ Error al inicializar la base de datos: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    # Permitir elegir entre modo producción y testing
    testing_mode = len(sys.argv) > 1 and sys.argv[1] == "--testing"
    
    if testing_mode:
        logger.info("🧪 Inicializando base de datos en modo TESTING")
        init_db(testing=True)
    else:
        logger.info("🚀 Inicializando base de datos en modo PRODUCCIÓN (MariaDB)")
        init_db(testing=False)
