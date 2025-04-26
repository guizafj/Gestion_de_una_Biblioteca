from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
import re
import secrets
from extensions import db, mail
import bcrypt
from sqlalchemy.orm import validates
from flask import url_for, current_app, render_template
from flask_mail import Message
import logging
import urllib.parse  # Añadir esta importación 

logging.basicConfig(filename='app.log', level=logging.INFO)

class Libro(db.Model):
    """
    Representa un libro en la biblioteca.
    """
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True) # Índice para ISBN
    titulo = db.Column(db.String(100), nullable=False, index=True) # Índice para título
    autor = db.Column(db.String(100), nullable=False, index=True) # Índice para autor
    autor = db.Column(db.String(100), nullable=False, index=True) # Índice para autor - no es unico
    cantidad = db.Column(db.Integer, nullable=False)
    disponible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Libro {self.titulo}>"

    @staticmethod
    def validar_isbn(isbn, libro_id=None):
        """
        Valida que el ISBN tenga 10 o 13 dígitos y sea único en la base de datos.
        Args:
            isbn (str): El ISBN a validar.
            libro_id (int): El ID del libro actual (opcional, para excluirlo de la validación).
        Returns:
            str: El ISBN validado.
        Raises:
            ValueError: Si el ISBN no es válido o ya existe en la base de datos.
        """
        # Validar que el ISBN no esté vacío
        if not isbn or isbn.strip() == "":
            raise ValueError("El ISBN no puede estar vacío.")
        
        # Validar formato del ISBN
        pattern = r"^\d{10}$|^\d{13}$"
        if not re.match(pattern, isbn):
            raise ValueError("El ISBN debe tener 10 o 13 dígitos.")

        # Validar unicidad del ISBN
        libro = Libro.query.filter_by(isbn=isbn).first()
        if libro and (libro_id is None or libro.id != libro_id):
            raise ValueError("El ISBN ya existe en la base de datos.")

        return isbn

    @staticmethod
    def validar_titulo(titulo, libro_id=None):
        """
        Valida que el título no esté duplicado en la base de datos.
        Args:
            titulo (str): El título a validar.
            libro_id (int): El ID del libro actual (opcional, para excluirlo de la validación).
        Returns:
            str: El título validado.
        Raises:
            ValueError: Si el título ya existe en la base de datos.
        """
        # Verificar que el título no esté vacío
        if not titulo or titulo.strip() == "":
            raise ValueError("El título no puede estar vacío.")
        
        # Validar formato del titulo (solo letras, espacios y caracteres especiales básicos)
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-]+$", titulo):
            raise ValueError("El autor solo puede contener letras, espacios, puntos y guiones.")

    
        # Validar unicidad del título
        libro = Libro.query.filter_by(titulo=titulo).first()
        if libro and (libro_id is None or libro.id != libro_id):
            raise ValueError("El título ya existe en la base de datos.")
        return titulo
    
    @staticmethod
    def validar_autor(autor):
        """
        Valida que el autor no esté vacío y tenga un formato adecuado.
        Args:
            autor (str): El autor a validar.
        Returns:
            str: El autor validado.
        Raises:
            ValueError: Si el autor no es válido.
        """
        # Verificar que el autor no esté vacío
        if not autor or autor.strip() == "":
            raise ValueError("El autor no puede estar vacío.")
        
        # Validar formato del autor (solo letras, espacios y caracteres especiales básicos)
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-]+$", autor):
            raise ValueError("El autor solo puede contener letras, espacios, puntos y guiones.")

        return autor
  
    @staticmethod
    def validar_cantidad(cantidad):
        """
        Valida que la cantidad sea un número entero positivo.
        Args:
            cantidad (int): La cantidad a validar.
        Returns:
            int: La cantidad validada.
        Raises:
            ValueError: Si la cantidad no es válida.
        """
        # Verificar que la cantidad no esté vacía
        if cantidad is None or str(cantidad).strip() == "":
            raise ValueError("La cantidad no puede estar vacía.")

        # Verificar que la cantidad sea un número entero
        if not str(cantidad).isdigit():
            raise ValueError("La cantidad debe ser un número entero.")

        # Verificar que la cantidad sea mayor que 0
        cantidad = int(cantidad)
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")

        return cantidad

    @classmethod
    def contar_libros(cls):
        """
        Cuenta el número total de libros en la biblioteca.
        """
        return cls.query.count()


class Usuario(UserMixin, db.Model):
    """
    Representa un usuario en la aplicación.
    """
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    __contrasena_hash = db.Column(db.String(255), nullable=False)  # Aumentado a 255
    rol = db.Column(db.String(20), default='usuario')
    email_confirmado = db.Column(db.Boolean, default=False)
    token_confirmacion = db.Column(db.String(100), nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    cuenta_bloqueada_hasta = db.Column(db.DateTime, nullable=True)
    token_expiracion = db.Column(db.DateTime, nullable=True)

    ROLES = {
        'usuario': 'Usuario regular',
        'bibliotecario': 'Bibliotecario',
        'admin': 'Administrador'
    }

    def __repr__(self):
        return f"<Usuario {self.nombre} ({self.rol})>"

    @validates('email')
    def validar_email(self, key, email):
        """
        Valida que el correo electrónico tenga un formato válido.
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("El correo electrónico no tiene un formato válido.")
        if Usuario.query.filter_by(email=email).first():
            raise ValueError("El correo electrónico ya está registrado.")
        return email

    @validates('nombre')
    def validar_nombre(self, key, nombre):
        """
        Valida que el nombre tenga una longitud adecuada y solo contenga caracteres permitidos.
        """
        if len(nombre) > 100:
            raise ValueError("El nombre no puede tener más de 100 caracteres.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise ValueError("El nombre solo puede contener letras y espacios.")
        return nombre

    @property
    def contrasena_hash(self):
        """
        Evita el acceso directo al hash de la contraseña.
        """
        raise AttributeError("El acceso directo al hash de la contraseña no está permitido.")

    def set_password(self, password):
        """
        Hashea y almacena la contraseña.
        """
        from werkzeug.security import generate_password_hash
        self.__contrasena_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado.
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.__contrasena_hash, password)

    def generar_token_confirmacion(self, expiracion=3600):
        """
        Genera un token único para confirmar el correo electrónico del usuario.
        Args:
            expiracion (int): Tiempo en segundos hasta que expire el token
        Returns:
            str: Token generado
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
        """
        try:
            with current_app.app_context():
                # Generar el enlace
                enlace = url_for(ruta, token=token, _external=True)
                
                # Renderizar la plantilla
                cuerpo_html = render_template(f"emails/{plantilla}", mensaje=mensaje, enlace=enlace)
                
                # Crear el mensaje
                msg = Message(
                    subject=asunto,
                    recipients=[email],
                    sender=current_app.config['MAIL_DEFAULT_SENDER']
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
            ValueError: Si el token no es válido o ha expirado
        """
        try:
            if not self.token_confirmacion or not self.token_expiracion:
                raise ValueError("El token de confirmación no es válido o ya ha sido utilizado.")
            
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
        """
        return self.email_confirmado and self.token_confirmacion is None
    
    def limitador_inicio(self):
        """
        Verifica si el usuario ha excedido el límite de intentos fallidos y bloquea la cuenta si es necesario.
        """
        if self.intentos_fallidos >= 5:  # Límite de intentos fallidos
            self.bloquear_cuenta()  # Bloquea la cuenta utilizando el método existente
            logging.warning(f"Cuenta bloqueada: {self.email}")
            return True  # Indica que la cuenta ha sido bloqueada
        return False  # Indica que la cuenta no está bloqueada

    @classmethod
    def crear_usuario(cls, nombre, email, contrasena, rol='usuario'):
        """
        Crea un nuevo usuario con el hash de la contraseña.
        """
        if not contrasena:
            raise ValueError("La contraseña no puede estar vacía.")
        usuario = cls(
            nombre=nombre,
            email=email,
            rol=rol
        )
        usuario.set_password(contrasena)  # Usar el método set_password para establecer el hash

        Usuario.enviar_correo(
            email=usuario.email,
            token=usuario.generar_token_confirmacion(),
            ruta="confirmar_email",
            asunto="Confirmación de correo electrónico",
            mensaje="Por favor, confirma tu correo electrónico haciendo clic en el siguiente enlace:",
            plantilla="confirmar_email.html"
        )

        return usuario

    @classmethod
    def restablecer_contrasena(cls, email):
        """
        Envía un correo electrónico para restablecer la contraseña del usuario.
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
            plantilla="restablecer_contrasena.html"
        )

    def tiene_rol(self, rol):
        """
        Verifica si el usuario tiene un rol específico.
        Args:
            rol (str): Rol a verificar ('usuario', 'bibliotecario', 'admin')
        Returns:
            bool: True si el usuario tiene el rol, False en caso contrario
        """
        return self.rol == rol

    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.tiene_rol('admin')
    
    def es_bibliotecario(self):
        """Verifica si el usuario es bibliotecario"""
        return self.tiene_rol('bibliotecario')
    
    def es_usuario_regular(self):
        """Verifica si el usuario es un usuario regular"""
        return self.tiene_rol('usuario')

    def bloquear_cuenta(self, duracion_bloqueo=300):
        """
        Bloquea temporalmente la cuenta del usuario.
        """
        if self.intentos_fallidos >= 5:  # Solo bloquear después de 5 intentos fallidos
            self.cuenta_bloqueada_hasta = datetime.now(timezone.utc) + timedelta(seconds=duracion_bloqueo)
            db.session.commit()

    def esta_bloqueada(self):
        """
        Verifica si la cuenta está bloqueada.
        """
        return self.cuenta_bloqueada_hasta and datetime.now(timezone.utc) < self.cuenta_bloqueada_hasta

    def resetear_intentos_fallidos(self):
        """
        Restablece el contador de intentos fallidos.
        """
        self.intentos_fallidos = 0
        db.session.commit()


class Prestamo(db.Model):
    """
    Representa un préstamo de un libro.
    """
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_prestamo = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_devolucion = db.Column(db.DateTime, nullable=True)

    libro = db.relationship('Libro', backref=db.backref('prestamos', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('prestamos', lazy=True))

    def __repr__(self):
        return f"<Prestamo {self.libro.titulo} a {self.usuario.nombre}>"

    def duracion_prestamo(self):
        """
        Calcula la duración del préstamo en días.
        """
        if not self.fecha_prestamo:
            raise ValueError("La fecha de préstamo no está definida.")
        fecha_fin = self.fecha_devolucion or datetime.now(timezone.utc)
        return (fecha_fin - self.fecha_prestamo).days