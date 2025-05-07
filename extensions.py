from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Instancia compartida de SQLAlchemy
db = SQLAlchemy()
 
# Instancia compartida de Flask-Mail
mail = Mail()