from modules.models_usuario import Usuario

def load_user(user_id):
    """ 
    Función que  carga un usuario de la base de datos.
    Flask-Login usa esta función para cargar el usuario durante la sesión.
    """
    return Usuario.query.get(int(user_id)) # Buscamos el usuario por su id
    # Si no existe, devuelve None
    # Si existe, devuelve el objeto Usuario correspondiente
    # El objeto Usuario es una instancia de la clase Usuario que representa