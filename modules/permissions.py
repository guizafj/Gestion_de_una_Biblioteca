from flask import redirect, url_for, flash
from flask_login import current_user
from functools import wraps
import logging
 
ROLES_PERMITIDOS = {
    'admin': ['gestionar_usuarios', 'cambiar_rol'],
    'bibliotecario': ['agregar_libro', 'editar_libro', 'eliminar_libro', 'gestion_libros', 'prestar', 'devolver'],
    'usuario': ['reservar', 'historial', 'recordatorios']}

# Decorador personalizado para restringir acceso por rol
def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder.', 'warning')
                return redirect(url_for('login'))
                
            if not any(current_user.tiene_rol(rol) for rol in roles):
                logging.warning(f"Intento de acceso no autorizado: {current_user.email}")
                flash('No tiene permisos para acceder a esta página.', 'danger')
                return redirect(url_for('index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
