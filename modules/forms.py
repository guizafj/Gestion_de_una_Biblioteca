import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from modules.models_libro import Libro  # Importar el modelo Libro


class RegistroForm(FlaskForm):
    """
    Formulario de registrar nuevos usuarios campos:
        - nombre: nombre del usuario
        - email: email del usuario
        - contraseña: contraseña del usuario
        - confirmar_contraseña: confirmar contraseña del usuario
        - rol: rol del usuario('admin', 'bibliotecario', 'usuario')
    """
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    confirmar_contrasena = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('contrasena', message='Las contraseñas deben coincidir.')])
    rol = SelectField('Rol', choices=[('usuario', 'Usuario'), ('bibliotecario', 'Bibliotecario')], default='usuario')
    submit = SubmitField('Registrarse')

    def validate_nombre(self, nombre):
        """
        Valida el nombre del usuario, solo permite letras y espacios
        """
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre.data):
            raise ValidationError('El nombre solo puede contener letras y espacios.')


class LoginForm(FlaskForm):
    """
    Formulario de inicio de sesión campos:
        - email: email del usuario
        - contraseña: contraseña del usuario
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Iniciar Sesión')


class AgregarLibroForm(FlaskForm):
    """
    Formulario para agregar un libro
    """
    isbn = StringField('ISBN', validators=[DataRequired(), Length(min=10, max=13)])
    titulo = StringField('Título', validators=[DataRequired()])
    autor = StringField('Autor', validators=[DataRequired()])
    editorial = StringField('Editorial', validators=[DataRequired()])
    genero = StringField('Genero', validators=[DataRequired()])
    cantidad = StringField('Cantidad', validators=[DataRequired()])
    submit = SubmitField('Agregar Libro')

    def validate_isbn(self, isbn):
        """
        Valida que el ISBN no exista en la base de datos.
        """
        try:
            Libro.validar_isbn(isbn.data)  # Reutiliza el método del modelo
        except ValueError as e:
            raise ValidationError(str(e))
   
    def validate_titulo(self, titulo):
        """
        Valida que el título no exista en la base de datos.
        """
        try:
            Libro.validar_titulo(titulo.data)  # Reutiliza el método del modelo
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_autor(self, autor):
        """
        Valida que el autor tenga un formato adecuado.
        """
        try:
            Libro.validar_autor(autor.data)
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_genero(self, genero):
        """Validar que genero tendo un formato adecuado"""
        try:
            Libro.validar_genero(genero.data)
        except ValueError as e:
            raise ValidationError(str(e))
        
    def validate_editorial(self, editorial):
        """Método para validad que la entrada de editorial tenga un formato adecuado"""
        try:
            Libro.validar_editorial(editorial.data)
        except ValueError as e:
            raise ValidationError(str(e))

    def validate_cantidad(self, cantidad):
        """
        Valida que la cantidad sea un número entero positivo.
        """
        try:
            Libro.validar_cantidad(cantidad.data)
        except ValueError as e:
            raise ValidationError(str(e))

class EditarLibroForm(FlaskForm):
    """
    Formulario para editar un libro
    """
    isbn = StringField('ISBN', validators=[DataRequired(), Length(min=10, max=13)])  # ISBN debe tener entre 10 y 13 caracteres
    titulo = StringField('Título', validators=[DataRequired()])
    autor = StringField('Autor', validators=[DataRequired()])
    genero = StringField('Genero', validators=[DataRequired()])
    editorial = StringField('Editorial', validators=[DataRequired()])
    cantidad = StringField('Cantidad', validators=[DataRequired()])
    submit = SubmitField('Actualizar Libro')

    def __init__(self, libro_id=None, *args, **kwargs):
        """
        Constructor para pasar el ID del libro que se está editando.
        """
        super().__init__(*args, **kwargs)
        self.libro_id = libro_id

    def validate_isbn(self, isbn):
        """
        Valida que el ISBN no exista en la base de datos para otro libro.
        """
        try:
            Libro.validar_isbn(isbn.data, libro_id=self.libro_id)  # Reutiliza el método del modelo
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_titulo(self, titulo):
        """
        Valida que el título no exista en la base de datos para otro libro.
        """
        try:
            Libro.validar_titulo(titulo.data, libro_id=self.libro_id)  # Reutiliza el método del modelo
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_autor(self, autor):
        """
        Valida que el autor tenga un formato adecuado.
        """
        try:
            Libro.validar_autor(autor.data)
        except ValueError as e:
            raise ValidationError(str(e))        
     
    def validate_genero(self, genero):
        """Validar que genero tendo un formato adecuado"""
        try:
            Libro.validar_genero(genero.data)
        except ValueError as e:
            raise ValidationError(str(e))
        
    def validate_editorial(self, editorial):
        """Valida que editorial tenga un formato adecuado"""
        try:
            Libro.validar_editorial(editorial.data)
        except ValueError as e:
            raise ValidationError(str(e))

    def validate_cantidad(self, cantidad):
        """
        Valida que la cantidad sea un número entero positivo.
        """
        try:
            Libro.validar_cantidad(cantidad.data)
        except ValueError as e:
            raise ValidationError(str(e))
        

class BuscarLibroForm(FlaskForm):
    """
    Formulario para buscar libros
    """
    termino = StringField('Buscar', validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField('Buscar')

class BuscarUsuarioForm(FlaskForm):
    """
    Formulario para buscar usuarios
    """
    termino = StringField('Buscar', validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField('Buscar')