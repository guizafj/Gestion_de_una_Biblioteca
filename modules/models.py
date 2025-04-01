from app import db
from flask_login import UserMixin
from datetime import datetime
import re
import secrets

class Libro(db.Model):
    """
    Representa un libro en la biblioteca.
    Atributos:
        id: ID único del libro.
        isbn: ISBN del libro (único).
        titulo: Título del libro.
        autor: Autor del libro.
        disponible: Indica si el libro está disponible para préstamo.
    """
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    disponible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Libro {self.titulo}>"

    @staticmethod
    def validar_isbn(isbn):
        """Valida que el ISBN tenga 10 o 13 dígitos."""
        pattern = r"^\d{10}$|^\d{13}$"
        return bool(re.match(pattern, isbn))

    @staticmethod
    def contar_libros():
        """Cuenta el número total de libros en la biblioteca."""
        return Libro.query.count()

    @staticmethod
    def validar_titulo(titulo):
        """Valida que el título no esté duplicado."""
        return not Libro.query.filter_by(titulo=titulo).first()

class Usuario(UserMixin, db.Model):
    """
    Representa un usuario en la aplicación.
    Atributos:
        id: ID único del usuario.
        nombre: Nombre del usuario.
        email: Email del usuario (único).
        contrasena: Contraseña del usuario.
        rol: Rol del usuario ('bibliotecario' o 'usuario').
        email_confirmado: Indica si el correo ha sido confirmado.
        token_confirmacion: Token único para confirmar el correo.
    """
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='usuario')  # Roles: 'bibliotecario' o 'usuario'
    email_confirmado = db.Column(db.Boolean, default=False)  # Nuevo campo
    token_confirmacion = db.Column(db.String(100), nullable=True)  # Nuevo campo

    def generar_token_confirmacion(self):
        """
        Genera un token único para confirmar el correo.
        """
        self.token_confirmacion = secrets.token_urlsafe(32)  # Genera un token seguro
        db.session.commit()
        return self.token_confirmacion

    def confirmar_email(self):
        """
        Marca el correo del usuario como confirmado.
        """
        self.email_confirmado = True
        self.token_confirmacion = None  # Elimina el token después de la confirmación
        db.session.commit()


    def __repr__(self):
        return f"<Usuario {self.nombre} ({self.rol})>"

    def es_bibliotecario(self):
        """
        Verifica si el usuario tiene el rol de bibliotecario.
        """
        return self.rol == 'bibliotecario'

class Prestamo(db.Model):
    """
    Representa un préstamo de un libro.
    Atributos:
        id: ID único del préstamo.
        libro_id: ID del libro prestado.
        usuario_id: ID del usuario que solicitó el préstamo.
        fecha_prestamo: Fecha en que se realizó el préstamo.
        fecha_devolucion: Fecha en que se devolvió el libro (opcional).
    """
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_prestamo = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devolucion = db.Column(db.DateTime, nullable=True)

    libro = db.relationship('Libro', backref='prestamos')  # Relación con el modelo Libro
    usuario = db.relationship('Usuario', backref='prestamos')  # Relación con el modelo Usuario

    def __repr__(self):
        return f"<Prestamo {self.libro.titulo} a {self.usuario.nombre}>"