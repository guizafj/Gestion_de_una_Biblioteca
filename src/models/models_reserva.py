"""
Módulo de modelo de datos para reservas en la aplicación de gestión de biblioteca.

Define la clase Reserva, que representa la solicitud de reserva de un libro por parte de un usuario,
junto con métodos y validaciones para gestionar el ciclo de vida de la reserva.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from extensions import db
from datetime import datetime, timezone, timedelta
from sqlalchemy import exc


class Reserva(db.Model):
    """
    Modelo que representa una solicitud de reserva de un libro.

    Atributos:
        id (int): Identificador único de la reserva.
        libro_id (int): ID del libro reservado.
        usuario_id (int): ID del usuario que realiza la reserva.
        fecha_reserva (datetime): Fecha y hora en que se realizó la reserva.
        estado (str): Estado de la reserva ('pendiente', 'aprobada', 'rechazada').
    """

    __tablename__ = "reserva"

    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(
        db.Integer, db.ForeignKey("libro.id", ondelete="CASCADE"), nullable=True
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=True
    )
    fecha_reserva = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado = db.Column(
        db.String(20), default="pendiente"
    )  # Estados posibles: pendiente, aprobada, rechazada

    # Relaciones con otros modelos
    libro = db.relationship("Libro", backref=db.backref("reservas", lazy=True))
    usuario = db.relationship("Usuario", backref=db.backref("reservas", lazy=True))

    def __repr__(self):
        """
        Representación legible del objeto Reserva para depuración.
        """
        libro_titulo = self.libro.titulo if self.libro else "Libro no disponible"
        usuario_nombre = (
            self.usuario.nombre if self.usuario else "Usuario no disponible"
        )
        return f"<Reserva {libro_titulo} por {usuario_nombre}>"

    @staticmethod
    def validar_reserva(libro_id):
        """
        Valida si un libro puede ser reservado.

        Args:
            libro_id (int): ID del libro a reservar.

        Raises:
            ValueError: Si el libro no existe o no está disponible para reserva.
        """
        # Importación local para evitar dependencias circulares
        from src.models.models_libro import Libro

        libro = Libro.query.get(libro_id)
        if not libro:
            raise ValueError("El libro no existe.")
        # Se llama como propiedad, no como método
        if not libro.esta_disponible:
            raise ValueError("El libro no está disponible para reserva.")

    @staticmethod
    def expirar_reservas():
        """
        Marca como expiradas (rechazadas) las reservas que no se han aprobado después de un período de tiempo.

        El período de expiración es de 7 días desde la fecha de reserva.
        """
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)
        reservas_expiradas = Reserva.query.filter(
            Reserva.estado == "pendiente", Reserva.fecha_reserva < fecha_limite
        ).all()
        for reserva in reservas_expiradas:
            reserva.estado = "rechazada"
        try:
            db.session.commit()
        except exc.SQLAlchemyError:
            db.session.rollback()
            raise  # Eliminamos la variable `e` porque no se usa
