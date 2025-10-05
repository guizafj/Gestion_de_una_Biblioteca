"""
Módulo de permisos y control de acceso por roles para la aplicación de biblioteca.

Define el decorador personalizado `requiere_rol` para restringir el acceso a rutas
según el rol del usuario autenticado. Incluye un diccionario de roles permitidos
y las acciones asociadas a cada uno.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from flask import redirect, url_for, flash
from flask_login import current_user
from functools import wraps
import logging

# Diccionario que asocia roles con las acciones permitidas
ROLES_PERMITIDOS = {
    "admin": ["gestionar_usuarios", "cambiar_rol"],
    "bibliotecario": [
        "agregar_libro",
        "editar_libro",
        "eliminar_libro",
        "gestion_libros",
        "prestar",
        "devolver",
    ],
    "usuario": ["reservar", "historial", "recordatorios"],
}


def requiere_rol(*roles):
    """
    Decorador para restringir el acceso a rutas según el rol del usuario.

    Args:
        *roles (str): Uno o más roles permitidos para acceder a la función decorada.

    Returns:
        function: Función decorada que verifica el rol antes de ejecutar la vista.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verifica si el usuario está autenticado
            if not current_user.is_authenticated:
                flash("Debe iniciar sesión para acceder.", "warning")
                return redirect(url_for("login"))

            # Verifica si el usuario tiene alguno de los roles requeridos
            if not any(current_user.tiene_rol(rol) for rol in roles):
                logging.warning(
                    f"Intento de acceso no autorizado: {current_user.email}"
                )
                flash("No tiene permisos para acceder a esta página.", "danger")
                return redirect(url_for("index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator
