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

    # Validación personalizada para verificar si el email ya existe
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('El email ya está registrado. Por favor, usa otro.')

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

    def validate_titulo(self, field):
        if not Libro.validar_titulo(field.data):
            raise ValidationError('Ya existe un libro con este título. Por favor, elige otro.')