from extensions import db
from datetime import datetime, timezone
from datetime import datetime, timezone, timedelta  # Correct import
from sqlalchemy import exc  # Import SQLAlchemy exceptions

class Reserva(db.Model):
    """
    Representa una solicitud de reserva de un libro.
    """
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id', ondelete='CASCADE'), nullable=False)  # Añadido ondelete
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)  # Añadido ondelete
    fecha_reserva = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado = db.Column(db.String(20), default='pendiente')  # Estados: pendiente, aprobada, rechazada

    libro = db.relationship('Libro', backref=db.backref('reservas', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('reservas', lazy=True))

    def __repr__(self):
        libro_titulo = self.libro.titulo if self.libro else "Libro no disponible"
        usuario_nombre = self.usuario.nombre if self.usuario else "Usuario no disponible"
        return f"<Reserva {libro_titulo} por {usuario_nombre}>"
    
    @staticmethod
    def validar_reserva(libro_id):
        """
        Valida si un libro puede ser reservado.
        """
        from modules.models_libro import Libro  # Local import
        libro = Libro.query.get(libro_id)
        if not libro:
            raise ValueError("El libro no existe.")
        if not libro.esta_disponible():  # Llama al método como función
            raise ValueError("El libro no está disponible para reserva.")
        
    @staticmethod
    def expirar_reservas():
        """
        Marca como expiradas las reservas que no se han aprobado después de un período de tiempo.
        """
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)  # Ejemplo: 7 días
        reservas_expiradas = Reserva.query.filter(
            Reserva.estado == 'pendiente',
            Reserva.fecha_reserva < fecha_limite
        ).all()
        for reserva in reservas_expiradas:
            reserva.estado = 'rechazada'
        # ... dentro de expirar_reservas():
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise  # Re-raise the exception to be handled elsewhere