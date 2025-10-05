"""
Módulo de formularios para la aplicación de gestión de biblioteca.

Este módulo define los formularios utilizados en la aplicación, incluyendo
validaciones personalizadas para los campos de cada formulario. Los formularios
se utilizan para registrar usuarios, iniciar sesión, agregar y editar libros,
buscar libros y crear usuarios desde el panel de administración.

Autor: Tu Francisco Javier
Fecha: 2025-05-17
"""

import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    ValidationError,
    SelectField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length
from src.models.models_libro import (
    Libro,
)  # Importa el modelo Libro para validaciones relacionadas

# Este archivo contiene los formularios utilizados en la aplicación.
# Los formularios son clases que definen los campos que los usuarios deben completar
# y las validaciones que se aplican a esos campos.


class RegistroForm(FlaskForm):
    """
    Formulario para registrar nuevos usuarios.

    Campos:
        nombre: Nombre del usuario (2-50 caracteres, solo letras y espacios).
        email: Dirección de correo electrónico válida.
        contrasena: Contraseña del usuario (mínimo 8 caracteres).
        confirmar_contrasena: Confirmación de la contraseña (debe coincidir).
        rol: Rol del usuario ('usuario', 'bibliotecario').
    """

    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    contrasena = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8)])
    confirmar_contrasena = PasswordField(
        "Confirmar Contraseña",
        validators=[
            DataRequired(),
            EqualTo("contrasena", message="Las contraseñas deben coincidir."),
        ],
    )
    rol = SelectField(
        "Rol",
        choices=[("usuario", "Usuario"), ("bibliotecario", "Bibliotecario")],
        default="usuario",
    )
    submit = SubmitField("Registrarse")

    def validate_nombre(self, nombre):
        """
        Valida que el nombre solo contenga letras y espacios.

        Args:
            nombre (Field): Campo de nombre del formulario.

        Raises:
            ValidationError: Si el nombre contiene caracteres no permitidos.
        """
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre.data):
            raise ValidationError("El nombre solo puede contener letras y espacios.")


class LoginForm(FlaskForm):
    """
    Formulario para iniciar sesión.

    Campos:
        email: Dirección de correo electrónico válida.
        contrasena: Contraseña del usuario (mínimo 8 caracteres).
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    contrasena = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField("Iniciar Sesión")


class AgregarLibroForm(FlaskForm):
    """
    Formulario para agregar un nuevo libro a la biblioteca.

    Campos:
        isbn: Código ISBN del libro (10-13 caracteres).
        titulo: Título del libro.
        autor: Autor del libro.
        editorial: Editorial del libro.
        genero: Género literario del libro.
        cantidad: Cantidad de copias disponibles (entero positivo).
    """

    isbn = StringField("ISBN", validators=[DataRequired(), Length(min=10, max=13)])
    titulo = StringField("Título", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    editorial = StringField("Editorial", validators=[DataRequired()])
    genero = StringField("Genero", validators=[DataRequired()])
    cantidad = StringField("Cantidad", validators=[DataRequired()])
    submit = SubmitField("Agregar Libro")

    def validate_isbn(self, isbn):
        """
        Valida que el ISBN no exista ya en la base de datos y sea válido.

        Args:
            isbn (Field): Campo ISBN del formulario.

        Raises:
            ValidationError: Si el ISBN es inválido o ya existe.
        """
        try:
            Libro.validar_isbn(isbn.data)
        except ValueError as e:
            raise ValidationError(str(e))

    def validate_cantidad(self, cantidad):
        """
        Valida que la cantidad sea un número entero positivo.

        Args:
            cantidad (Field): Campo cantidad del formulario.

        Raises:
            ValidationError: Si la cantidad no es válida.
        """
        try:
            Libro.validar_cantidad(cantidad.data)
        except ValueError as e:
            raise ValidationError(str(e))


class EditarLibroForm(FlaskForm):
    """
    Formulario para editar la información de un libro existente.

    Campos:
        isbn: Código ISBN del libro.
        titulo: Título del libro.
        autor: Autor del libro.
        editorial: Editorial del libro.
        genero: Género literario del libro.
        cantidad: Cantidad de copias disponibles.
    """

    isbn = StringField("ISBN", validators=[DataRequired(), Length(min=10, max=13)])
    titulo = StringField("Título", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    editorial = StringField("Editorial", validators=[DataRequired()])
    genero = StringField("Genero", validators=[DataRequired()])
    cantidad = StringField("Cantidad", validators=[DataRequired()])
    submit = SubmitField("Actualizar Libro")

    def __init__(self, libro_id=None, *args, **kwargs):
        """
        Constructor para pasar el ID del libro que se está editando.

        Args:
            libro_id (int, optional): ID del libro a editar.
        """
        super().__init__(*args, **kwargs)
        self.libro_id = libro_id

    def validate_isbn(self, isbn):
        """
        Valida que el ISBN no exista en la base de datos para otro libro.

        Args:
            isbn (Field): Campo ISBN del formulario.

        Raises:
            ValidationError: Si el ISBN ya existe para otro libro.
        """
        try:
            Libro.validar_isbn(isbn.data, libro_id=self.libro_id)
        except ValueError as e:
            raise ValidationError(str(e))


class BuscarLibroForm(FlaskForm):
    """
    Formulario para buscar libros en la biblioteca.

    Campos:
        termino: Término de búsqueda (puede ser título, autor, etc.).
    """

    termino = StringField("Buscar", validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField("Buscar")


class CrearUsuarioForm(FlaskForm):
    """
    Formulario para crear un nuevo usuario desde el panel de administración.

    Campos:
        nombre: Nombre del usuario.
        email: Dirección de correo electrónico válida.
        contrasena: Contraseña del usuario.
        confirmar_contrasena: Confirmación de la contraseña.
        rol: Rol del usuario ('usuario', 'bibliotecario').
    """

    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    contrasena = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8)])
    confirmar_contrasena = PasswordField(
        "Confirmar Contraseña",
        validators=[
            DataRequired(),
            EqualTo("contrasena", message="Las contraseñas deben coincidir."),
        ],
    )
    rol = SelectField(
        "Rol",
        choices=[("usuario", "Usuario"), ("bibliotecario", "Bibliotecario")],
        default="usuario",
    )
    submit = SubmitField("Crear Usuario")
