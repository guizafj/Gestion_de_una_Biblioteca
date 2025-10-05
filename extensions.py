"""
Módulo de extensiones para la aplicación Flask de gestión de biblioteca.

Define e inicializa las extensiones compartidas que se usan en toda la aplicación,
como SQLAlchemy para la base de datos y Flask-Mail para el envío de correos.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Instancia compartida de SQLAlchemy para la gestión de la base de datos
db = SQLAlchemy()

# Instancia compartida de Flask-Mail para el envío de correos electrónicos
mail = Mail()
