from main import create_app
from extensions import db, mail
from src.models.models_usuario import Usuario
from flask_mail import Message
from flask import url_for
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener credenciales del administrador desde variables de entorno
admin_email = os.getenv('ADMIN_EMAIL', 'admin@biblioteca.libro')
admin_password = os.getenv('ADMIN_PASSWORD', 'TuContraseñaSegura')

def crear_admin():
    """
    Crea un usuario administrador inicial y envía el correo de confirmación.
    """
    try:
        app = create_app()
        
        with app.app_context():
            # Verificar si ya existe un administrador
            if Usuario.query.filter_by(rol="admin").first():
                logger.info("Ya existe un usuario administrador. No se creará uno nuevo.")
                return
            
            # Crear un administrador inicial
            admin = Usuario(
                nombre="Administrador",
                email=admin_email,
                rol="admin"
            )
            
            # Establecer la contraseña utilizando el método set_password
            admin.set_password(admin_password)  # Contraseña predeterminada
            
            # Agregar y guardar el administrador en la base de datos
            db.session.add(admin)
            db.session.commit()
            logger.info("Administrador creado exitosamente.")

            # Generar token de confirmación
            token = admin.generar_token_confirmacion()
            
            # Generar enlace de confirmación
            enlace = url_for('auth.confirmar_email', token=token, _external=True)
            
            # Crear mensaje de correo
            msg = Message(
                subject="Confirmación de cuenta",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[admin.email],
                charset='utf-8'
            )
            
            # HTML template
            msg.html = f"""
            <!DOCTYPE html>
            <html lang="es">
                <head>
                    <meta charset="utf-8">
                    <style>
                        .button {{
                            background-color: #4CAF50;
                            border: none;
                            color: white;
                            padding: 15px 32px;
                            text-align: center;
                            text-decoration: none;
                            display: inline-block;
                            font-size: 16px;
                            margin: 4px 2px;
                            cursor: pointer;
                            border-radius: 4px;
                        }}
                    </style>
                </head>
                <body>
                    <p>Haga clic en el siguiente enlace para confirmar su cuenta:</p>
                    <p><a href="{enlace}" class="button">Confirmar cuenta</a></p>
                    <p>O copie y pegue el siguiente enlace en su navegador:</p>
                    <p>{enlace}</p>
                </body>
            </html>
            """
            
            # Versión texto plano
            msg.body = f"Para confirmar su cuenta, visite: {enlace}"
            
            # Enviar el correo
            mail.send(msg)
            logger.info(f"Correo de confirmación enviado a {admin.email}")
            
    except Exception as e:
        logger.error(f"Error al crear administrador: {str(e)}")
        raise

if __name__ == "__main__":
    crear_admin()