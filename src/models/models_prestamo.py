"""
Módulo de modelo de datos para préstamos en la aplicación de gestión de biblioteca.

Define la clase Prestamo, que representa el préstamo de un libro a un usuario,
junto con métodos y validaciones para gestionar el ciclo de vida del préstamo,
incluyendo fechas, estado, penalizaciones y recordatorios.

Autor: Francisco Javier
Fecha: 2025-05-17
"""

from datetime import datetime, timezone, timedelta
import sqlalchemy as sa
from extensions import db


class Prestamo(db.Model):
    """
    Modelo que representa un préstamo de un libro en la biblioteca.

    Atributos:
        id (int): Identificador único del préstamo.
        libro_id (int): ID del libro prestado.
        usuario_id (int): ID del usuario que realiza el préstamo.
        fecha_prestamo (datetime): Fecha y hora en que se realizó el préstamo.
        fecha_devolucion (datetime): Fecha y hora en que se devolvió el libro.
        estado (str): Estado del préstamo ('activo', 'devuelto', 'vencido').
    """

    __tablename__ = "prestamo"

    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(
        db.Integer, db.ForeignKey("libro.id", ondelete="SET NULL"), nullable=True
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=True
    )
    fecha_prestamo = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),  # Valor predeterminado en Python
        server_default=sa.text(
            "CURRENT_TIMESTAMP"
        ),  # Valor predeterminado en la base de datos
    )
    fecha_devolucion = db.Column(db.DateTime, nullable=True)
    estado = db.Column(
        db.String(20), default="activo"
    )  # Estados: activo, devuelto, vencido

    # Relaciones con otros modelos
    libro = db.relationship("Libro", backref=db.backref("prestamos", lazy=True))
    usuario = db.relationship("Usuario", backref=db.backref("prestamos", lazy=True))

    def __repr__(self):
        """
        Representación legible del objeto Prestamo para depuración.
        """
        return f"<Prestamo {self.libro.titulo} a {self.usuario.nombre}>"

    def duracion_prestamo(self):
        """
        Calcula la duración del préstamo en días.

        Returns:
            int: Número de días entre el préstamo y la devolución (o fecha actual).
        Raises:
            ValueError: Si la fecha de préstamo no está definida.
        """
        if not self.fecha_prestamo:
            raise ValueError("La fecha de préstamo no está definida.")
        fecha_fin = self.fecha_devolucion or datetime.now(timezone.utc)
        return (fecha_fin - self.fecha_prestamo).days

    def calcular_fecha_vencimiento(self, dias_prestamo=14):
        """
        Calcula la fecha de vencimiento del préstamo.

        Args:
            dias_prestamo (int): Días permitidos para el préstamo.

        Returns:
            datetime: Fecha de vencimiento.
        """
        return self.fecha_prestamo + timedelta(days=dias_prestamo)

    def esta_vencido(self, dias_prestamo=14):
        """
        Verifica si el préstamo está vencido.

        Args:
            dias_prestamo (int): Días permitidos para el préstamo.

        Returns:
            bool: True si el préstamo está vencido, False en caso contrario.
        """
        fecha_vencimiento = self.calcular_fecha_vencimiento(dias_prestamo)
        return datetime.now(timezone.utc) > fecha_vencimiento

    def marcar_como_devuelto(self):
        """
        Marca el préstamo como devuelto y actualiza la cantidad disponible del libro.

        Raises:
            ValueError: Si el préstamo ya ha sido devuelto.
        """
        if self.fecha_devolucion:
            raise ValueError("El préstamo ya ha sido devuelto.")
        self.fecha_devolucion = datetime.now(timezone.utc)
        self.estado = "devuelto"
        self.libro.incrementar_cantidad()
        db.session.commit()

    @staticmethod
    def prestamos_activos(usuario_id):
        """
        Devuelve el número de préstamos activos de un usuario.

        Args:
            usuario_id (int): ID del usuario.

        Returns:
            int: Número de préstamos activos.
        """
        return Prestamo.query.filter_by(usuario_id=usuario_id, estado="activo").count()

    @staticmethod
    def validar_prestamo(usuario_id, limite_prestamos=3):
        """
        Valida si un usuario puede realizar un nuevo préstamo.

        Args:
            usuario_id (int): ID del usuario.
            limite_prestamos (int): Límite de préstamos permitidos.

        Raises:
            ValueError: Si el usuario ha alcanzado el límite de préstamos.
        """
        prestamos_activos = Prestamo.query.filter_by(
            usuario_id=usuario_id, estado="activo"
        ).count()
        if prestamos_activos >= limite_prestamos:
            raise ValueError(
                "El usuario ha alcanzado el límite de préstamos permitidos."
            )

    @staticmethod
    def enviar_recordatorio(prestamo):
        """
        Envía un recordatorio al usuario sobre un préstamo próximo a vencer.

        Args:
            prestamo (Prestamo): Objeto préstamo al que se le enviará el recordatorio.
        """
        from flask_mail import Message
        from extensions import mail

        usuario = prestamo.usuario
        fecha_vencimiento = prestamo.calcular_fecha_vencimiento()
        mensaje = Message(
            subject="Recordatorio de Préstamo",
            recipients=[usuario.email],
            body=(
                f"Hola {usuario.nombre}, recuerda que el préstamo del libro "
                f"'{prestamo.libro.titulo}' vence el {fecha_vencimiento.strftime('%Y-%m-%d')}."
            ),
        )
        mail.send(mensaje)

    @staticmethod
    def libros_mas_prestados():
        """
        Devuelve los libros más prestados.

        Returns:
            list: Lista de tuplas (libro_id, total_prestamos).
        """
        return (
            db.session.query(
                Prestamo.libro_id, db.func.count(Prestamo.id).label("total_prestamos")
            )
            .join(Prestamo.libro)
            .group_by(Prestamo.libro_id)
            .order_by(db.desc("total_prestamos"))
            .all()
        )

    def calcular_penalizacion(self, tarifa_por_dia=1):
        """
        Calcula la penalización por días de retraso.

        Args:
            tarifa_por_dia (int): Monto a cobrar por cada día de retraso.

        Returns:
            int: Monto total de la penalización.
        """
        if self.esta_vencido():
            dias_retraso = (
                datetime.now(timezone.utc) - self.calcular_fecha_vencimiento()
            ).days
            return dias_retraso * tarifa_por_dia
        return 0


# Mover los imports al inicio del archivo para evitar E402
from src.models.models_libro import Libro
from src.models.models_usuario import Usuario
