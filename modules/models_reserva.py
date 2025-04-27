from extensions import db
from datetime import datetime, timezone

class Reserva(db.Model):
    """
    Representa una solicitud de reserva de un libro.
    """
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_reserva = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado = db.Column(db.String(20), default='pendiente')  # Estados: pendiente, aprobada, rechazada

    libro = db.relationship('Libro', backref=db.backref('reservas', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('reservas', lazy=True))

    def __repr__(self):
        return f"<Reserva {self.libro.titulo} por {self.usuario.nombre}>"