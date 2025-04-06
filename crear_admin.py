from app import create_app
from extensions import db, mail
from modules.models import Usuario
from flask_mail import Message
from flask import url_for
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_admin():
    """
    Crea un usuario administrador inicial y envía el correo de confirmación.
    """
    try:
        app = create_app()
        
        with app.app_context():
            # Crear un administrador inicial
            admin = Usuario(
                nombre="Administrador",
                email="soporte@ecolibri.art",
                rol="admin"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

            # Generar token y enviar correo
            token = admin.generar_token_confirmacion()
            
            # Generar enlace sin codificación adicional
            enlace = url_for('confirmar_email', token=token, _external=True)
            
            # Crear mensaje
            msg = Message(
                subject="Confirmacion de cuenta",
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
            logger.info(f"Administrador creado exitosamente. Correo enviado a {admin.email}")
            
    except Exception as e:
        logger.error(f"Error al crear administrador: {str(e)}")
        raise

if __name__ == "__main__":
    crear_admin()