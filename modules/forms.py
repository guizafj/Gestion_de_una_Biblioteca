import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length


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
    contrasena = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8, message='La contraseña debe tener al menos 8 caracteres.')])
    confirmar_contrasena = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('contrasena', message='Las contraseñas deben coincidir')])
    rol = SelectField('Rol', choices=[('usuario', 'Usuario'), ('bibliotecario', 'Bibliotecario')], default='usuario', validators=[DataRequired()])
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
    isbn = StringField('ISBN', validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired()])
    autor = StringField('Autor', validators=[DataRequired()])
    submit = SubmitField('Agregar Libro')


class EditarLibroForm(FlaskForm):
    """
    Formulario para editar un libro
    """
    isbn = StringField('ISBN', validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired()])
    autor = StringField('Autor', validators=[DataRequired()])
    submit = SubmitField('Actualizar Libro')