from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import SelectField

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
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    confirmar_contrasena = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('contrasena')])
    rol = SelectField('Rol', choices=[('usuario', 'Usuario'), ('bibliotecario', 'Bibliotecario')], default='usuario')
    submit = SubmitField('Registrarse')

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