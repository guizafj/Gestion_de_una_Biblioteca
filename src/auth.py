"""
Módulo de autenticación para la integración con Flask-Login.

Define la función necesaria para que Flask-Login pueda cargar usuarios
desde la base de datos durante la gestión de sesiones.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from src.models.models_usuario import Usuario


def load_user(user_id):
    """
    Carga un usuario de la base de datos por su ID.

    Flask-Login utiliza esta función para recuperar el usuario asociado
    a una sesión activa.

    Args:
        user_id (int): ID del usuario a cargar.

    Returns:
        Usuario | None: Instancia del usuario si existe, None si no existe.
    """
    return Usuario.query.get(int(user_id))
    # Si no existe, devuelve None.
    # Si existe, devuelve el objeto Usuario correspondiente.
