from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
import re
import secrets
from extensions import db, mail
import bcrypt
from sqlalchemy.orm import validates
from flask import url_for
from flask_mail import Message

class Libro(db.Model):
    """
    Representa un libro en la biblioteca.
    """
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False index=True) # Índice para ISBN
    titulo = db.Column(db.String(100), nullable=False index=True) # Índice para título
    autor = db.Column(db.String(100), nullable=False index=True) # Índice para autor
    disponible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Libro {self.titulo}>"

    @validates('isbn')
    def validar_isbn(self, key, isbn):
        """
        Valida que el ISBN tenga 10 o 13 dígitos y sea único en la base de datos.
        """
        pattern = r"^\d{10}$|^\d{13}$"
        if not re.match(pattern, isbn):
            raise ValueError("El ISBN debe tener 10 o 13 dígitos.")
        if Libro.query.filter_by(isbn=isbn).first():
            raise ValueError("El ISBN ya existe en la base de datos.")
        return isbn

    @staticmethod
    def validar_titulo(titulo):
        """
        Valida que el título no esté duplicado.
        """
        if Libro.query.filter_by(titulo=titulo).first():
            raise ValueError("El título ya existe en la base de datos.")
        return True

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
    nombre = db.Column(db.String(100), nullable=False)  # Asegúrate de que admita Unicode
    email = db.Column(db.String(120), unique=True, nullable=False)
    __contrasena_hash = db.Column(db.String(60), nullable=False)
    rol = db.Column(db.String(20), default='usuario')  # Roles: 'usuario', 'bibliotecario', 'admin'
    email_confirmado = db.Column(db.Boolean, default=False)
    token_confirmacion = db.Column(db.String(100), nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    cuenta_bloqueada_hasta = db.Column(db.DateTime, nullable=True)

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

    def set_password(self, contrasena):
        """
        Genera un hash seguro para la contraseña.
        """
        if not contrasena:
            raise ValueError("La contraseña no puede estar vacía.")
        if len(contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        self.__contrasena_hash = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, contrasena):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado.
        """
        if not contrasena:
            return False
        return bcrypt.checkpw(contrasena.encode('utf-8'), self.__contrasena_hash.encode('utf-8'))

    def generar_token_confirmacion(self, expiracion=3600):
        """
        Genera un token único para confirmar el correo electrónico del usuario.
        """
        self.token_confirmacion = secrets.token_urlsafe(32).encode('utf-8').decode('utf-8')  # Asegura UTF-8
        self.token_expiracion = datetime.utcnow() + timedelta(seconds=expiracion)
        db.session.commit()
        return self.token_confirmacion

    def confirmar_email(self):
        """
        Marca el correo del usuario como confirmado y elimina el token de confirmación.
        """
        if not self.token_expiracion:
            raise ValueError("El token de confirmación no es válido o ya ha sido utilizado.")
        if datetime.utcnow() > self.token_expiracion:
            raise ValueError("El token ha expirado.")
        self.email_confirmado = True
        self.token_confirmacion = None
        self.token_expiracion = None
        db.session.commit()

    def correo_confirmado(self):
        """
        Verifica si el correo electrónico del usuario ha sido confirmado.
        """
        return self.email_confirmado and self.token_confirmacion is None
    
    @staticmethod
    def enviar_correo(email, token, ruta, asunto, mensaje):
        """
        Envía un correo electrónico con un enlace generado dinámicamente.
        """
        try:
            enlace = url_for(ruta, token=token, _external=True)
            msg = Message(asunto, recipients=[email])
            msg.body = f"{mensaje}\n\n{enlace}"
            mail.send(msg)
        except Exception as e:
            logging.error(f"Error al enviar correo a {email}: {e}")
            raise ValueError("Ocurrió un error al enviar el correo. Intenta nuevamente.")
    
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
        return usuario

    def tiene_rol(self, rol):
        """
        Verifica si el usuario tiene un rol específico.
        """
        return self.rol == rol

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