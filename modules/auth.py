from flask_login import UserMixin  # Clase para manejar la autenticación de usuarios
from modules.models import Usuario  # Importamos el modelo Usuario

def load_user(user_id):
    """
    Función que carga un usuario desde la base de datos.
    Flask-Login usa esta función para cargar el usuario actual durante la sesión.
    """
    return Usuario.query.get(int(user_id))  # Buscamos el usuario por su ID

