import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import SelectField
from modules.models import Usuario
from modules.models import Libro

class RegistroForm(FlaskForm):
    """
    Formulario para registrar nuevos usuarios.
    Campos:
        nombre: Nombre del usuario.
        email: Email del usuario.
        contrasena: Contraseña del usuario.
        confirmar_contrasena: Confirmación de contraseña.
        rol: Rol del usuario ('bibliotecario' o 'usuario').
    """
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[ 
        DataRequired(),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres.")
    ])
    confirmar_contrasena = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('contrasena', message="Las contraseñas deben coincidir.")
    ])
    rol = SelectField('Rol', choices=[('usuario', 'Usuario'), ('bibliotecario', 'Bibliotecario')], default='usuario', validators=[DataRequired()])
    submit = SubmitField('Registrarse')

    def validate_nombre(self, nombre):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre.data):
            raise ValidationError("El nombre solo puede contener letras y espacios.")
        
class LoginForm(FlaskForm):
    """
    Formulario para iniciar sesión.
    Campos:
        email: Email del usuario.
        contrasena: Contraseña del usuario.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class AgregarLibroForm(FlaskForm):
    isbn = StringField('ISBN', validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired()])
    autor = StringField('Autor', validators=[DataRequired()])
    submit = SubmitField('Agregar Libro')

class EditarLibroForm(FlaskForm):
    isbn = StringField('ISBN', validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired()])
    autor = StringField('Autor', validators=[DataRequired()])
    submit = SubmitField('Guardar Cambios')
