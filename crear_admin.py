from app import create_app
from extensions import db
from modules.models import Usuario

app = create_app()

with app.app_context():
    # Crear un administrador inicial
    admin = Usuario.crear_usuario(
        nombre="Administrador",
        email="soporte@ecolibri.art",
        contrasena="admin123",
        rol="admin"
    )
    db.session.add(admin)
    db.session.commit()
    print("Administrador inicial creado con éxito.")