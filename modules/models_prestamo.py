from extensions import db
from datetime import datetime, timezone, timedelta

class Prestamo(db.Model):
    """
    Representa un préstamo de un libro.
    """
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_prestamo = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_devolucion = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), default='activo')  # Estados: activo, devuelto, vencido

    libro = db.relationship('Libro', backref=db.backref('prestamos', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('prestamos', lazy=True))

    def __repr__(self):
        return f"<Prestamo {self.libro.titulo} a {self.usuario.nombre}>"

    def duracion_prestamo(self):
        """
        Calcula la duración del préstamo en días.
        """
        if not self.fecha_prestamo:
            raise ValueError("La fecha de préstamo no está definida.")
        fecha_fin = self.fecha_devolucion or datetime.now(timezone.utc)
        return (fecha_fin - self.fecha_prestamo).days

    def calcular_fecha_vencimiento(self, dias_prestamo=14):
        """
        Calcula la fecha de vencimiento del préstamo.
        """
        return self.fecha_prestamo + timedelta(days=dias_prestamo)

    def esta_vencido(self, dias_prestamo=14):
        """
        Verifica si el préstamo está vencido.
        """
        fecha_vencimiento = self.calcular_fecha_vencimiento(dias_prestamo)
        return datetime.now(timezone.utc) > fecha_vencimiento

    def marcar_como_devuelto(self):
        """
        Marca el préstamo como devuelto y actualiza la cantidad disponible del libro.
        """
        if self.fecha_devolucion:
            raise ValueError("El préstamo ya ha sido devuelto.")
        self.fecha_devolucion = datetime.now(timezone.utc)
        self.estado = 'devuelto'
        self.libro.incrementar_cantidad()
        db.session.commit()

    @staticmethod
    def prestamos_activos(usuario_id):
        """
        Devuelve el número de préstamos activos de un usuario.
        """
        return Prestamo.query.filter_by(usuario_id=usuario_id, estado='activo').count()

    @staticmethod
    def validar_prestamo(usuario_id, limite_prestamos=3):
        """
        Valida si un usuario puede realizar un nuevo préstamo.
        """
        prestamos_activos = Prestamo.query.filter_by(usuario_id=usuario_id, estado='activo').count()
        if prestamos_activos >= limite_prestamos:
            raise ValueError("El usuario ha alcanzado el límite de préstamos permitidos.")

    @staticmethod
    def enviar_recordatorio(prestamo):
        """
        Envía un recordatorio al usuario sobre un préstamo próximo a vencer.
        """
        from flask_mail import Message
        from extensions import mail

        usuario = prestamo.usuario
        fecha_vencimiento = prestamo.calcular_fecha_vencimiento()
        mensaje = Message(
            subject="Recordatorio de Préstamo",
            recipients=[usuario.email],
            body=f"Hola {usuario.nombre}, recuerda que el préstamo del libro '{prestamo.libro.titulo}' vence el {fecha_vencimiento.strftime('%Y-%m-%d')}."
        )
        mail.send(mensaje)

    @staticmethod
    def libros_mas_prestados():
        """
        Devuelve los libros más prestados.
        """
        return db.session.query(
            Prestamo.libro_id, db.func.count(Prestamo.id).label('total_prestamos')
        ).join(Prestamo.libro).group_by(Prestamo.libro_id).order_by(db.desc('total_prestamos')).all()

    def calcular_penalizacion(self, tarifa_por_dia=1):
        """
        Calcula la penalización por días de retraso.
        """
        if self.esta_vencido():
            dias_retraso = (datetime.now(timezone.utc) - self.calcular_fecha_vencimiento()).days
            return dias_retraso * tarifa_por_dia
        return 0