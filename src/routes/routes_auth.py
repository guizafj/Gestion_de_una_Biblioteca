"""
Módulo de rutas de autenticación para la aplicación de gestión de biblioteca.

Este módulo define las rutas relacionadas con el registro, inicio de sesión,
confirmación de correo, recuperación y restablecimiento de contraseña, y cierre
de sesión de los usuarios.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required  # Eliminamos current_user porque no se usa
from src.models.models_usuario import Usuario
from src.forms.forms import RegistroForm, LoginForm
from extensions import db
import logging
import re
from datetime import datetime, timedelta

# Crear el Blueprint para autenticación
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Ruta para registrar un nuevo usuario.

    - Valida el formulario de registro.
    - Verifica si el correo ya está registrado.
    - Crea un nuevo usuario y genera un token de confirmación.
    - Envía un correo de confirmación.
    """
    breadcrumbs = [
        {"name": "Inicio", "url": url_for("generales.index")},
        {"name": "Registro", "url": url_for("auth.registro")},
    ]
    form = RegistroForm()
    if form.validate_on_submit():
        # Verificar si el correo ya está registrado
        if Usuario.query.filter_by(email=form.email.data).first():
            flash("El correo electrónico ya está registrado.", "warning")
            return redirect(url_for("auth.registro"))

        # Crear un nuevo usuario
        nuevo_usuario = Usuario(
            nombre=form.nombre.data, email=form.email.data, rol=form.rol.data
        )
        nuevo_usuario.set_password(form.contrasena.data)

        # Generar token de confirmación
        token = nuevo_usuario.generar_token_confirmacion()
        nuevo_usuario.token_confirmacion = token
        nuevo_usuario.token_expiracion = datetime.utcnow() + timedelta(hours=24)

        db.session.add(nuevo_usuario)
        db.session.commit()

        # Enviar correo de confirmación
        try:
            Usuario.enviar_correo(
                email=nuevo_usuario.email,
                token=token,
                ruta="auth.confirmar_email",
                asunto="Confirmación de correo electrónico",
                mensaje="Para confirmar tu correo electrónico, haz clic en el siguiente enlace:",
                plantilla="confirmar_email.html",
            )
        except Exception as e:
            logging.error(f"Error al enviar el correo de confirmación: {e}")
            flash(
                "No se pudo enviar el correo de confirmación. Por favor, intenta nuevamente.",
                "danger",
            )
            return redirect(url_for("auth.registro"))

        flash(
            "Usuario registrado exitosamente, confirma tu correo electrónico.",
            "success",
        )
        return redirect(url_for("auth.login"))
    return render_template("registro.html", form=form)


@auth_bp.route("/confirmar_email/<token>")
def confirmar_email(token):
    """
    Ruta para confirmar el correo electrónico del usuario usando el token.

    - Busca el usuario por el token.
    - Verifica si el token es válido y no ha expirado.
    - Marca el correo como confirmado.
    """
    breadcrumbs = [
        {"name": "Inicio", "url": url_for("generales.index")},
        {
            "name": "Confirmar Email",
            "url": url_for("auth.confirmar_email", token=token),
        },
    ]
    try:
        usuario = Usuario.query.filter_by(token_confirmacion=token).first()
        if not usuario:
            return render_template(
                "confirmar_email.html",
                error="El enlace de confirmación no es válido.",
                breadcrumbs=breadcrumbs,
            )

        if datetime.utcnow() > usuario.token_expiracion:
            return render_template(
                "confirmar_email.html",
                error="El enlace de confirmación ha expirado.",
                breadcrumbs=breadcrumbs,
            )

        usuario.email_confirmado = True
        usuario.token_confirmacion = None
        usuario.token_expiracion = None
        db.session.commit()

        flash("Tu correo electrónico ha sido confirmado correctamente.", "success")
        return redirect(url_for("auth.login"))

    except Exception as e:
        logging.error(f"Error al confirmar el correo: {e}")
        return render_template(
            "confirmar_email.html",
            error="Ha ocurrido un error al confirmar tu correo electrónico.",
            breadcrumbs=breadcrumbs,
        )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Ruta para iniciar sesión de usuario.

    - Valida el formulario de inicio de sesión.
    - Verifica si el usuario existe y si el correo está confirmado.
    - Verifica la contraseña y realiza el login.
    """
    breadcrumbs = [
        {"name": "Inicio", "url": url_for("generales.index")},
        {"name": "Iniciar Sesión", "url": url_for("auth.login")},
    ]
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario:
            if not usuario.email_confirmado:
                flash(
                    "Debes confirmar tu correo electrónico antes de iniciar sesión.",
                    "warning",
                )
                return redirect(url_for("auth.login"))

            if usuario.check_password(form.contrasena.data):
                login_user(usuario)
                flash("Inicio de sesión exitoso.", "success")
                return redirect(url_for("generales.index"))
            else:
                flash("Credenciales incorrectas. Intenta nuevamente.", "warning")
        else:
            flash("No se encontró una cuenta con ese correo electrónico.", "danger")
    return render_template("login.html", form=form, breadcrumbs=breadcrumbs)


@auth_bp.route("/logout")
@login_required
def logout():
    """
    Ruta para cerrar la sesión del usuario actual.
    """
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/recuperar_cuenta", methods=["GET", "POST"])
def recuperar_cuenta():
    """
    Ruta para solicitar un enlace de recuperación de contraseña.

    - Valida el correo electrónico ingresado.
    - Si existe, genera un token y envía un correo con el enlace de recuperación.
    """
    breadcrumbs = [
        {"name": "Inicio", "url": url_for("generales.index")},
        {"name": "Recuperar Cuenta", "url": url_for("auth.recuperar_cuenta")},
    ]
    if request.method == "POST":
        try:
            email = request.form.get("email").strip()

            # Validar formato del correo electrónico
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not email or not re.match(pattern, email):
                flash("Por favor, ingresa un correo electrónico válido.", "warning")
                return redirect(url_for("auth.recuperar_cuenta"))

            usuario = Usuario.query.filter_by(email=email).first()
            if not usuario:
                flash("El correo electrónico no está registrado.", "warning")
                return redirect(url_for("auth.recuperar_cuenta"))

            # Generar token y enviar correo
            token = usuario.generar_token_confirmacion()

            Usuario.enviar_correo(
                email=usuario.email,
                token=token,
                ruta="restablecer_contrasena",
                asunto="Recuperación de contraseña",
                mensaje="Para restablecer tu contraseña, haz clic en el siguiente enlace:",
                plantilla="restablecer_contrasena.html",
            )
            flash(
                "Se ha enviado un enlace de recuperación a tu correo electrónico.",
                "info",
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            logging.error(f"Error en recuperación de cuenta: {e}")
            flash("Ocurrió un error. Por favor, intenta nuevamente.", "danger")

    return render_template("recuperar_cuenta.html")


@auth_bp.route("/restablecer_contrasena/<token>", methods=["GET", "POST"])
def restablecer_contrasena(token):
    """
    Ruta para restablecer la contraseña usando un token válido.

    - Verifica que el token sea válido y no haya expirado.
    - Permite al usuario ingresar una nueva contraseña.
    """
    breadcrumbs = [
        {"name": "Inicio", "url": url_for("generales.index")},
        {"name": "Recuperar Cuenta", "url": url_for("auth.recuperar_cuenta")},
        {
            "name": "Restablecer Contraseña",
            "url": url_for("auth.restablecer_contrasena", token=token),
        },
    ]
    usuario = Usuario.query.filter_by(token_confirmacion=token).first()

    # Verificar si el token es válido
    if not usuario or datetime.utcnow() > usuario.token_expiracion:
        flash("El enlace de recuperación no es válido o ha expirado.", "danger")
        return redirect(url_for("auth.recuperar_cuenta"))

    if request.method == "POST":
        nueva_contrasena = request.form.get("contrasena").strip()

        # Validar la nueva contraseña
        if not nueva_contrasena or len(nueva_contrasena) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "warning")
            return redirect(url_for("auth.restablecer_contrasena", token=token))

        try:
            # Actualizar la contraseña del usuario
            usuario.set_password(nueva_contrasena)
            usuario.token_confirmacion = None
            usuario.token_expiracion = None
            db.session.commit()

            flash(
                "Tu contraseña ha sido restablecida con éxito. Ahora puedes iniciar sesión.",
                "success",
            )
            return redirect(url_for("auth.login"))
        except Exception as e:
            logging.error(f"Error al restablecer la contraseña: {e}")
            flash(
                "Ocurrió un error al restablecer tu contraseña. Intenta nuevamente más tarde.",
                "danger",
            )

    return render_template("restablecer_contrasena.html", token=token)
