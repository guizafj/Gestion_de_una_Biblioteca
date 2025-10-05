"""
Módulo de modelo de datos para usuarios en la aplicación de gestión de biblioteca.

Define la clase Usuario, que representa a los usuarios del sistema, junto con
métodos y validaciones para gestionar la autenticación, roles, confirmación de
correo, bloqueo de cuentas, reservas y notificaciones.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
import secrets
from extensions import db, mail
from flask import url_for, current_app, render_template
from flask_mail import Message
import logging
import re
from sqlalchemy.orm import validates

# Configuración básica de logging para registrar eventos importantes
logging.basicConfig(filename="app.log", level=logging.INFO)


class Usuario(UserMixin, db.Model):
    """
    Modelo que representa un usuario en la aplicación.

    Atributos:
        id (int): Identificador único del usuario.
        nombre (str): Nombre completo del usuario.
        email (str): Correo electrónico único del usuario.
        __contrasena_hash (str): Hash seguro de la contraseña.
        rol (str): Rol del usuario ('usuario', 'bibliotecario', 'admin').
        email_confirmado (bool): Indica si el correo fue confirmado.
        token_confirmacion (str): Token para confirmar el correo.
        intentos_fallidos (int): Número de intentos fallidos de inicio de sesión.
        cuenta_bloqueada_hasta (datetime): Fecha/hora hasta la que la cuenta está bloqueada.
        token_expiracion (datetime): Fecha/hora de expiración del token de confirmación.
    """

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    __contrasena_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default="usuario")
    email_confirmado = db.Column(db.Boolean, default=False)
    token_confirmacion = db.Column(db.String(100), nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    cuenta_bloqueada_hasta = db.Column(db.DateTime, nullable=True)
    token_expiracion = db.Column(db.DateTime, nullable=True)
    # reservas = db.relationship('Reserva', backref='usuario', cascade='all, delete-orphan')

    # Diccionario de roles disponibles
    ROLES = {
        "usuario": "Usuario regular",
        "bibliotecario": "Bibliotecario",
        "admin": "Administrador",
    }

    def __repr__(self):
        """
        Representación legible del objeto Usuario para depuración.
        """
        return f"<Usuario {self.nombre} ({self.rol})>"

    @validates("email")
    def validar_email(self, key, email):
        """
        Valida que el correo electrónico tenga un formato válido y no esté duplicado.

        Args:
            key (str): Nombre del campo.
            email (str): Correo electrónico a validar.

        Returns:
            str: Correo validado.

        Raises:
            ValueError: Si el formato es inválido o ya está registrado.
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValueError("El correo electrónico no tiene un formato válido.")
        if Usuario.query.filter_by(email=email).first():
            raise ValueError("El correo electrónico ya está registrado.")
        return email

    @validates("nombre")
    def validar_nombre(self, key, nombre):
        """
        Valida que el nombre tenga una longitud adecuada y solo contenga caracteres permitidos.

        Args:
            key (str): Nombre del campo.
            nombre (str): Nombre a validar.

        Returns:
            str: Nombre validado.

        Raises:
            ValueError: Si el nombre es demasiado largo o contiene caracteres no permitidos.
        """
        if len(nombre) > 100:
            raise ValueError("El nombre no puede tener más de 100 caracteres.")
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
            raise ValueError("El nombre solo puede contener letras y espacios.")
        return nombre

    @property
    def contrasena_hash(self):
        """
        Evita el acceso directo al hash de la contraseña.
        """
        raise AttributeError(
            "El acceso directo al hash de la contraseña no está permitido."
        )

    def set_password(self, password):
        """
        Hashea y almacena la contraseña del usuario.

        Args:
            password (str): Contraseña en texto plano.
        """
        from werkzeug.security import generate_password_hash

        self.__contrasena_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado.

        Args:
            password (str): Contraseña en texto plano.

        Returns:
            bool: True si la contraseña es correcta, False en caso contrario.
        """
        from werkzeug.security import check_password_hash

        return check_password_hash(self.__contrasena_hash, password)

    def generar_token_confirmacion(self, expiracion=3600):
        """
        Genera un token único para confirmar el correo electrónico del usuario.

        Args:
            expiracion (int): Tiempo en segundos hasta que expire el token.

        Returns:
            str: Token generado.

        Raises:
            ValueError: Si ocurre un error al generar el token.
        """
        try:
            self.token_confirmacion = secrets.token_urlsafe(32)
            self.token_expiracion = datetime.utcnow() + timedelta(seconds=expiracion)
            db.session.commit()
            logging.info(f"Token generado para usuario {self.email}")
            return self.token_confirmacion
        except Exception as e:
            error_msg = f"Error al generar token: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def enviar_correo(email, token, ruta, asunto, mensaje, plantilla):
        """
        Envía un correo electrónico utilizando una plantilla HTML.

        Args:
            email (str): Dirección de correo del destinatario.
            token (str): Token único para el enlace.
            ruta (str): Nombre de la ruta Flask para generar el enlace.
            asunto (str): Asunto del correo.
            mensaje (str): Mensaje adicional para el correo.
            plantilla (str): Nombre del archivo de plantilla HTML.

        Raises:
            ValueError: Si ocurre un error al enviar el correo.
        """
        try:
            with current_app.app_context():
                # Generar el enlace para el usuario
                enlace = url_for(ruta, token=token, _external=True)
                # Renderizar la plantilla HTML del correo
                cuerpo_html = render_template(
                    f"emails/{plantilla}", mensaje=mensaje, enlace=enlace
                )
                # Crear el mensaje de correo
                msg = Message(
                    subject=asunto,
                    recipients=[email],
                    sender=current_app.config["MAIL_DEFAULT_SENDER"],
                )
                msg.html = cuerpo_html
                msg.body = f"{mensaje}\n\nPara confirmar tu correo, visita: {enlace}"
                # Enviar el correo
                mail.send(msg)
                logging.info(f"Correo enviado exitosamente a {email}")
        except Exception as e:
            error_msg = f"Error al enviar correo a {email}: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)

    def confirmar_email(self):
        """
        Marca el correo del usuario como confirmado y elimina el token.

        Raises:
            ValueError: Si el token no es válido o ha expirado.
        """
        try:
            if not self.token_confirmacion or not self.token_expiracion:
                raise ValueError(
                    "El token de confirmación no es válido o ya ha sido utilizado."
                )
            if datetime.utcnow() > self.token_expiracion:
                raise ValueError("El token ha expirado.")
            self.email_confirmado = True
            self.token_confirmacion = None
            self.token_expiracion = None
            db.session.commit()
            logging.info(f"Email confirmado para usuario {self.email}")
        except Exception as e:
            error_msg = f"Error al confirmar email: {str(e)}"
            logging.error(error_msg)
            db.session.rollback()
            raise ValueError(error_msg)

    def correo_confirmado(self):
        """
        Verifica si el correo electrónico del usuario ha sido confirmado.

        Returns:
            bool: True si el correo está confirmado, False en caso contrario.
        """
        return self.email_confirmado and self.token_confirmacion is None

    @classmethod
    def crear_usuario(cls, nombre, email, contrasena, rol="usuario"):
        """
        Crea un nuevo usuario con el hash de la contraseña y envía correo de confirmación.

        Args:
            nombre (str): Nombre del usuario.
            email (str): Correo electrónico.
            contrasena (str): Contraseña en texto plano.
            rol (str): Rol del usuario.

        Returns:
            Usuario: Instancia del usuario creado.

        Raises:
            ValueError: Si la contraseña está vacía.
        """
        if not contrasena:
            raise ValueError("La contraseña no puede estar vacía.")
        usuario = cls(nombre=nombre, email=email, rol=rol)
        usuario.set_password(contrasena)
        Usuario.enviar_correo(
            email=usuario.email,
            token=usuario.generar_token_confirmacion(),
            ruta="confirmar_email",
            asunto="Confirmación de correo electrónico",
            mensaje="Por favor, confirma tu correo electrónico haciendo clic en el siguiente enlace:",
            plantilla="confirmar_email.html",
        )
        return usuario

    @classmethod
    def restablecer_contrasena(cls, email):
        """
        Envía un correo electrónico para restablecer la contraseña del usuario.

        Args:
            email (str): Correo electrónico del usuario.

        Raises:
            ValueError: Si el usuario no existe.
        """
        usuario = cls.query.filter_by(email=email).first()
        if not usuario:
            raise ValueError("No se encontró un usuario con ese correo electrónico.")
        Usuario.enviar_correo(
            email=usuario.email,
            token=usuario.generar_token_confirmacion(),
            ruta="restablecer_contrasena",
            asunto="Restablecimiento de contraseña",
            mensaje="Para restablecer tu contraseña, haz clic en el siguiente enlace:",
            plantilla="restablecer_contrasena.html",
        )

    @classmethod
    def recuperar_cuenta(cls, email):
        """
        Envía un correo electrónico para recuperar la cuenta del usuario.

        Args:
            email (str): Correo electrónico del usuario.

        Raises:
            ValueError: Si el usuario no existe.
        """
        usuario = cls.query.filter_by(email=email).first()
        if not usuario:
            raise ValueError("No se encontró un usuario con ese correo electrónico.")
        Usuario.enviar_correo(
            email=usuario.email,
            token=usuario.generar_token_confirmacion(),
            ruta="recuperar_cuenta",
            asunto="Recuperación de cuenta",
            mensaje="Para recuperar tu cuenta, haz clic en el siguiente enlace:",
            plantilla="recuperar_cuenta.html",
        )

    def tiene_rol(self, rol):
        """
        Verifica si el usuario tiene un rol específico.

        Args:
            rol (str): Rol a verificar ('usuario', 'bibliotecario', 'admin').

        Returns:
            bool: True si el usuario tiene el rol, False en caso contrario.
        """
        return self.rol == rol

    def es_admin(self):
        """
        Verifica si el usuario es administrador.

        Returns:
            bool: True si es admin, False en caso contrario.
        """
        return self.tiene_rol("admin")

    def es_bibliotecario(self):
        """
        Verifica si el usuario es bibliotecario.

        Returns:
            bool: True si es bibliotecario, False en caso contrario.
        """
        return self.tiene_rol("bibliotecario")

    def es_usuario_regular(self):
        """
        Verifica si el usuario es un usuario regular.

        Returns:
            bool: True si es usuario regular, False en caso contrario.
        """
        return self.tiene_rol("usuario")

    def limitador_inicio(self):
        """
        Verifica si el usuario ha excedido el límite de intentos fallidos y bloquea la cuenta si es necesario.

        Returns:
            bool: True si la cuenta ha sido bloqueada, False en caso contrario.
        """
        if self.intentos_fallidos >= 5:
            self.bloquear_cuenta()
            logging.warning(f"Cuenta bloqueada: {self.email}")
            return True
        return False

    def bloquear_cuenta(self, duracion_bloqueo=300):
        """
        Bloquea temporalmente la cuenta del usuario.

        Args:
            duracion_bloqueo (int): Duración del bloqueo en segundos.
        """
        if self.intentos_fallidos >= 5:
            self.cuenta_bloqueada_hasta = datetime.now(timezone.utc) + timedelta(
                seconds=duracion_bloqueo
            )
            db.session.commit()

    def esta_bloqueada(self):
        """
        Verifica si la cuenta está bloqueada.

        Returns:
            bool: True si la cuenta está bloqueada, False en caso contrario.
        """
        return (
            self.cuenta_bloqueada_hasta
            and datetime.now(timezone.utc) < self.cuenta_bloqueada_hasta
        )

    def resetear_intentos_fallidos(self):
        """
        Restablece el contador de intentos fallidos.
        """
        self.intentos_fallidos = 0
        db.session.commit()

    def tiene_reservas_activas(self):
        """
        Verifica si el usuario tiene reservas pendientes o aprobadas.

        Returns:
            bool: True si tiene reservas activas, False en caso contrario.
        """
        return any(
            reserva.estado in ["pendiente", "aprobada"] for reserva in self.reservas
        )

    def obtener_estadisticas_reservas(self):
        """
        Obtiene estadísticas de las reservas del usuario.

        Returns:
            dict: Diccionario con estadísticas de reservas.
        """
        return {
            "total": len(self.reservas),
            "pendientes": sum(1 for r in self.reservas if r.estado == "pendiente"),
            "aprobadas": sum(1 for r in self.reservas if r.estado == "aprobada"),
            "rechazadas": sum(1 for r in self.reservas if r.estado == "rechazada"),
        }

    def notificar_eliminacion(self):
        """
        Envía una notificación al usuario antes de que su cuenta sea eliminada.
        """
        try:
            mensaje = "Tu cuenta ha sido eliminada del sistema de la biblioteca."
            self.enviar_correo(
                email=self.email,
                token="",
                ruta="index",
                asunto="Eliminación de cuenta",
                mensaje=mensaje,
                plantilla="notificacion_general.html",
            )
            logging.info(f"Notificación de eliminación enviada a {self.email}")
        except Exception as e:
            logging.error(f"Error al enviar notificación de eliminación: {e}")
