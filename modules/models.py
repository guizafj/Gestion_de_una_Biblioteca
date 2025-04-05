from flask_login import UserMixin # Clase para manejar la autenticación de usuarios
from datetime import datetime, timezone
import re
import secrets
from extensions import db
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.orm import validates

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
        
        """
        Proporciona una representación en forma de cadena del objeto Libro.

            str: Una cadena con el formato "<Libro {self.titulo}>", donde `self.titulo`
            es el título del libro.
        """
        return f"<Libro {self.titulo}>"

    @validates('isbn')
    def validar_isbn(self, key, isbn):
        """
        Valida que el ISBN tenga 10 o 13 dígitos y sea único en la base de datos.
        """
        # Validar formato del ISBN
        pattern = r"^\d{10}$|^\d{13}$"
        if not re.match(pattern, isbn):
            raise ValueError("El ISBN debe tener 10 o 13 dígitos.")

        # Validar unicidad del ISBN
        if Libro.query.filter_by(isbn=isbn).first():
            raise ValueError("El ISBN ya existe en la base de datos.")
        
        return isbn
        
    @staticmethod
    def contar_libros():
        """Cuenta el número total de libros en la biblioteca."""
        return Libro.query.count()

    @staticmethod
    def validar_titulo(titulo):
        """
        Valida que el título no esté duplicado.
        """
        if Libro.query.filter_by(titulo=titulo).first():
            raise ValueError("El título ya existe en la base de datos.")
        return True

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
    __contrasena_hash = db.Column(db.String(60), nullable=False)  # Almacena el hash
    rol = db.Column(db.String(20), default='usuario')  # Roles: 'bibliotecario' o 'usuario'
    email_confirmado = db.Column(db.Boolean, default=False)  # Nuevo campo
    token_confirmacion = db.Column(db.String(100), nullable=True)  # Nuevo campo
    intentos_fallidos = db.Column(db.Integer, default=0)  # Número de intentos fallidos
    cuenta_bloqueada_hasta = db.Column(db.DateTime, nullable=True)  # Fecha y hora hasta la que la cuenta está bloqueada

    def __repr__(self):
        return f"<Usuario {self.nombre} ({self.rol})>"
    
    @validates('email')
    def validar_email(self, key, email):
        """
        Valida que el correo electrónico tenga un formato válido.
        Args:
            key (str): El nombre del atributo (en este caso, 'email').
            email (str): El correo electrónico a validar.
        Returns:
            str: El correo validado.
        Raises:
            ValueError: Si el correo no tiene un formato válido.
        """
        # Validar formato del correo
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("El correo electrónico no tiene un formato válido.")

        # Validar unicidad del correo
        if Usuario.query.filter_by(email=email).first():
            raise ValueError("El correo electrónico ya está registrado.")
        
        return email

    @validates('nombre')
    def validar_nombre(self, key, nombre):
        """
        Valida que el nombre tenga una longitud adecuada y solo contenga caracteres permitidos.
        Args:
            key (str): El nombre del atributo (en este caso, 'nombre').
            nombre (str): El nombre a validar.
        Returns:
            str: El nombre validado.
        Raises:
            ValueError: Si el nombre no cumple con las restricciones.
        """
        # Limitar la longitud del nombre
        if len(nombre) > 100:
            raise ValueError("El nombre no puede tener más de 100 caracteres.")
        
        # Validar que solo contenga letras y espacios
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
        Genera un hash seguro para la contraseña y lo guarda en la base de datos.
        Args:
            contrasena (str): La contraseña en texto plano.
        """
        if not contrasena:
            raise ValueError("La contraseña no puede estar vacía.")
        self.__contrasena_hash = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, contrasena):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado.
        Args:
            contrasena (str): La contraseña en texto plano.
        Returns:
            bool: True si la contraseña coincide, False en caso contrario.
        """
        if not contrasena:
            return False
        return bcrypt.checkpw(contrasena.encode('utf-8'), self.__contrasena_hash.encode('utf-8'))
       
    def generar_token_confirmacion(self, expiracion=3600):
        """
        Genera un token único para confirmar el correo electrónico del usuario.
        El token se almacena en la base de datos y se devuelve para su uso.
        Returns:
            str: El token generado.
        """
        self.token_confirmacion = secrets.token_urlsafe(32)
        self.token_expiracion = datetime.utcnow() + timedelta(seconds=expiracion)
        db.session.commit()  # Guarda los cambios en la base de datos
        return self.token_confirmacion
    
    def confirmar_email(self):
        """
        Marca el correo del usuario como confirmado y elimina el token de confirmación. 
        Raises:
        ValueError: Si el token ha expirado.
        """
        if not self.token_expiracion:
            raise ValueError("El token de confirmación no es válido o ya ha sido utilizado.")
    
        if datetime.utcnow() > self.token_expiracion:
            raise ValueError("El token ha expirado.")
        
        # Marcar el correo como confirmado
        self.email_confirmado = True
        
        # Eliminar el token y su expiración
        self.token_confirmacion = None
        self.token_expiracion = None
        
        # Guardar los cambios en la base de datos
        db.session.commit()

    def correo_confirmado(self):
        """
        Verifica si el correo electrónico del usuario ha sido confirmado.
        Returns:
            bool: True si el correo está confirmado, False en caso contrario.
        """
        return self.email_confirmado and self.token_confirmacion is None
    
    def es_bibliotecario(self):
        """
        Verifica si el usuario tiene el rol de bibliotecario.
        """
        return self.rol == 'bibliotecario'
    
    def bloquear_cuenta(self, duracion_bloqueo=300):
        """
        Bloquea temporalmente la cuenta del usuario.
        Args:
            duracion_bloqueo (int): Duración del bloqueo en segundos (por defecto 5 minutos).
        """
        self.cuenta_bloqueada_hasta = datetime.now(timezone.utc) + timedelta(seconds=duracion_bloqueo)
        db.session.commit()

    def esta_bloqueada(self):
        """
        Verifica si la cuenta está bloqueada.
        Returns:
            bool: True si la cuenta está bloqueada, False en caso contrario.
        """
        if self.cuenta_bloqueada_hasta and datetime.now(timezone.utc) < self.cuenta_bloqueada_hasta:
            return True
        return False

    def resetear_intentos_fallidos(self):
        """
        Restablece el contador de intentos fallidos.
        """
        self.intentos_fallidos = 0
        db.session.commit()
    
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
    fecha_prestamo = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_devolucion = db.Column(db.DateTime, nullable=True)

    libro = db.relationship('Libro', backref=db.backref('prestamos', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('prestamos', lazy=True))

    def __repr__(self):
        return f"<Prestamo {self.libro.titulo} a {self.usuario.nombre}>"

    def duracion_prestamo(self):
        """
        Calcula la duración del préstamo en días.
        Returns:
            int: Número de días que el libro ha estado prestado.
        """
        if not self.fecha_devolucion:
            return (datetime.now(timezone.utc) - self.fecha_prestamo).days
        return (self.fecha_devolucion - self.fecha_prestamo).days

   