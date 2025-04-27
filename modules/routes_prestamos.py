"""Modulo para las rutas de prestamos"""
from ast import mod
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
import logging
from urllib.parse import urlencode
from modules.models_prestamo import Prestamo
from modules.models_libro import Libro
from modules.models_usuario import Usuario
from modules.permissions import requiere_rol
from modules.models_reserva import Reserva

prestamos_bp = Blueprint('prestamos', __name__)

@prestamos_bp.route('/prestar/<int:libro_id>', methods=['GET', 'POST'])
@prestamos_bp.route('/prestar/<int:libro_id>/<int:reserva_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def prestar(libro_id, reserva_id=None):
    """
    Permite prestar un libro directamente o basado en una reserva aprobada.
    """
    libro = Libro.query.get_or_404(libro_id)
    reserva = None

    if reserva_id:
        reserva = Reserva.query.get_or_404(reserva_id)
        if reserva.estado != 'aprobada':
            flash('La reserva no está aprobada. No se puede realizar el préstamo.', 'warning')
            return redirect(url_for('prestamos.reservas_pendientes', breadcrumbs=breadcrumbs))

    if not libro.esta_disponible():
        flash('No hay ejemplares disponibles para préstamo.', 'warning')
        return redirect(url_for('prestamos.reservas_pendientes' if reserva else 'generales.index'))

    # Consultar usuarios solo si no hay reserva
    usuarios = Usuario.query.all() if not reserva else None

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')},
        {'name': 'Prestar Libro', 'url': url_for('prestamos.prestar', libro_id=libro_id)}
    ]

    if request.method == 'POST':
        try:
            usuario_id = reserva.usuario_id if reserva else request.form.get('usuario_id')
            Prestamo.validar_prestamo(usuario_id)

            prestamo = Prestamo(
                libro_id=libro.id,
                usuario_id=usuario_id
            )
            libro.reducir_cantidad()
            db.session.add(prestamo)
            db.session.commit()

            flash(f'Préstamo realizado para el libro "{libro.titulo}".', 'success')
            return redirect(url_for('generales.index'))
        except Exception as e:
            logging.error(f"Error al realizar el préstamo: {e}")
            flash("Ocurrió un error al realizar el préstamo. Intenta nuevamente.", "danger")

    return render_template('prestar_libro.html', libro=libro, reserva=reserva, usuarios=usuarios, breadcrumbs=breadcrumbs)

@prestamos_bp.route('/devolver/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def devolver(libro_id):
    """
    Permite devolver un libro prestado.
    Actualiza el estado del libro y registra la fecha de devolución.
    """
    libro = Libro.query.get_or_404(libro_id)
    prestamo = Prestamo.query.filter_by(libro_id=libro.id, fecha_devolucion=None).first()

    if not prestamo:
        flash('Este libro no está prestado actualmente.', 'warning')
        return redirect(url_for('generales.index'))

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')},
        {'name': 'Devolver Libro', 'url': url_for('prestamos.devolver', libro_id=libro_id)}
    ]

    if request.method == 'POST':
        try:
            prestamo.marcar_como_devuelto()  # Usar el método del modelo
            flash(f'Libro "{libro.titulo}" devuelto correctamente.', 'success')
            return redirect(url_for('generales.index'))
        except Exception as e:
            logging.error(f"Error al devolver libro: {e}")
            flash("Ocurrió un error al devolver el libro. Intenta nuevamente.", "danger")

    return render_template('devolver_libro.html', libro=libro, breadcrumbs=breadcrumbs)

@prestamos_bp.route('/recordatorios')
@login_required
def recordatorios():
    """
    Muestra recordatorios de préstamos pendientes.
    Incluye préstamos con más de 7 días sin devolución.
    """
    try:
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)
        prestamos_pendientes = Prestamo.query.options(joinedload(Prestamo.libro)).filter(
            Prestamo.usuario_id == current_user.id,
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_prestamo < fecha_limite
        ).all()

        breadcrumbs = [
            {'name': 'Inicio', 'url': url_for('generales.index')},
            {'name': 'Recordatorios', 'url': url_for('prestamos.recordatorios')}
        ]

        return render_template('recordatorios.html', prestamos_pendientes=prestamos_pendientes, breadcrumbs=breadcrumbs)
    except Exception as e:
        logging.error(f"Error al cargar recordatorios: {e}")
        flash("Ocurrió un error al cargar los recordatorios. Intenta nuevamente.", "danger")
        return redirect(url_for('generales.index'))

@prestamos_bp.route('/historial')
@login_required
def historial():
    """
    Muestra el historial de préstamos del usuario actual.
    Incluye todos los préstamos realizados por el usuario.
    """
    try:
        prestamos = Prestamo.query.options(joinedload(Prestamo.libro)).filter_by(usuario_id=current_user.id).all()
        params = {'usuario_id': current_user.id, 'total_prestamos': len(prestamos)}
        query_string = urlencode(params)

        breadcrumbs = [
            {'name': 'Inicio', 'url': url_for('generales.index')},
            {'name': 'Mi Historial', 'url': url_for('prestamos.historial')}
        ]

        return render_template('historial.html', prestamos=prestamos, breadcrumbs=breadcrumbs)
    except Exception as e:
        logging.error(f"Error al cargar historial: {e}")
        flash("Ocurrió un error al cargar el historial. Intenta nuevamente.", "danger")
        return redirect(url_for('generales.index'))

@prestamos_bp.route('/historial_prestamos')
@login_required
@requiere_rol('bibliotecario', 'admin')
def historial_prestamos():
    """
    Muestra el historial de préstamos de la biblioteca, incluyendo los libros más prestados.
    """
    # Obtener los libros más prestados
    libros_mas_prestados = Prestamo.libros_mas_prestados()

    # Obtener información detallada de los libros
    historial = []
    for libro_id, total_prestamos in libros_mas_prestados:
        libro = Libro.query.get(libro_id)
        if libro:
            historial.append({
                'titulo': libro.titulo,
                'autor': libro.autor,
                'total_prestamos': total_prestamos
            })

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Historial de Préstamos', 'url': url_for('prestamos.historial_prestamos')}
    ]

    return render_template('historial_prestamos.html', historial=historial, breadcrumbs=breadcrumbs)

@prestamos_bp.route('/reservar/<int:libro_id>', methods=['GET', 'POST'])
@login_required
def reservar(libro_id):
    """
    Permite a un usuario estándar reservar un libro.
    """
    libro = Libro.query.get_or_404(libro_id)

    if not libro.esta_disponible():
        flash('El libro no está disponible para reserva.', 'warning')
        return redirect(url_for('generales.index'))

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Reservar Libro', 'url': url_for('prestamos.reservar', libro_id=libro_id)}
    ]

    if request.method == 'POST':
        try:
            # Verificar si el usuario ya tiene una reserva pendiente para este libro
            reserva_existente = Reserva.query.filter_by(libro_id=libro.id, usuario_id=current_user.id, estado='pendiente').first()
            if reserva_existente:
                flash('Ya tienes una reserva pendiente para este libro.', 'warning')
                return redirect(url_for('generales.index'))

            # Crear la reserva
            reserva = Reserva(
                libro_id=libro.id,
                usuario_id=current_user.id
            )
            db.session.add(reserva)
            db.session.commit()

            flash(f'Reserva para el libro "{libro.titulo}" realizada correctamente.', 'success')
            return redirect(url_for('generales.index'))
        except Exception as e:
            logging.error(f"Error al reservar libro: {e}")
            flash("Ocurrió un error al reservar el libro. Intenta nuevamente.", "danger")

    return render_template('reservar_libro.html', libro=libro, breadcrumbs=breadcrumbs)

@prestamos_bp.route('/reservas_pendientes')
@login_required
@requiere_rol('bibliotecario', 'admin')
def reservas_pendientes():
    """
    Muestra todas las reservas pendientes para que el bibliotecario las gestione.
    """
    if not current_user.es_bibliotecario() and not current_user.es_admin():
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('generales.index'))

    reservas = Reserva.query.filter_by(estado='pendiente').all()

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')}
    ]

    return render_template('reservas_pendientes.html', reservas=reservas, breadcrumbs=breadcrumbs)

@prestamos_bp.route('/aprobar_reserva/<int:reserva_id>', methods=['POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def aprobar_reserva(reserva_id):
    """
    Permite al bibliotecario aprobar una reserva y crear un préstamo.
    """
    if not current_user.es_bibliotecario() and not current_user.es_admin():
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('generales.index'))

    reserva = Reserva.query.get_or_404(reserva_id)
    libro = reserva.libro

    if not libro.esta_disponible():
        flash('El libro ya no está disponible.', 'warning')
        breadcrumbs = [
            {'name': 'Inicio', 'url': url_for('generales.index')},
            {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')}
        ]
        return redirect(url_for('prestamos.reservas_pendientes', breadcrumbs=breadcrumbs))

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')},
        {'name': 'Aprobar Reserva', 'url': url_for('prestamos.aprobar_reserva', reserva_id=reserva_id)}
    ]

    try:
        # Crear el préstamo
        prestamo = Prestamo(
            libro_id=libro.id,
            usuario_id=reserva.usuario_id
        )
        libro.esta_disponible = False
        reserva.estado = 'aprobada'

        db.session.add(prestamo)
        db.session.commit()

        flash(f'Reserva aprobada y préstamo creado para el libro "{libro.titulo}".', 'success')
        return redirect(url_for('prestamos.reservas_pendientes', breadcrumbs=breadcrumbs))
    except Exception as e:
        logging.error(f"Error al aprobar reserva: {e}")
        flash("Ocurrió un error al aprobar la reserva. Intenta nuevamente.", "danger")
        return redirect(url_for('prestamos.reservas_pendientes', breadcrumbs=breadcrumbs))

@prestamos_bp.route('/rechazar_reserva/<int:reserva_id>', methods=['POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def rechazar_reserva(reserva_id):
    """
    Permite al bibliotecario rechazar una reserva.
    """
    if not current_user.es_bibliotecario() and not current_user.es_admin():
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('generales.index'))

    reserva = Reserva.query.get_or_404(reserva_id)

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')},
        {'name': 'Rechazar Reserva', 'url': url_for('prestamos.rechazar_reserva', reserva_id=reserva_id)}
    ]

    try:
        reserva.estado = 'rechazada'
        db.session.commit()

        flash(f'Reserva para el libro "{reserva.libro.titulo}" rechazada.', 'success')
        return redirect(url_for('prestamos.reservas_pendientes'))
    except Exception as e:
        logging.error(f"Error al rechazar reserva: {e}")
        flash("Ocurrió un error al rechazar la reserva. Intenta nuevamente.", "danger")
        return redirect(url_for('prestamos.reservas_pendientes', breadcrumbs=breadcrumbs))

@prestamos_bp.route('/gestionar_prestamos')
@login_required
@requiere_rol('bibliotecario', 'admin')
def gestionar_prestamos():
    """
    Muestra todos los préstamos activos para que el bibliotecario o administrador los gestione.
    """
    if not current_user.es_bibliotecario() and not current_user.es_admin():
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('generales.index'))

    # Obtener todos los préstamos activos (sin fecha de devolución)
    prestamos = Prestamo.query.options(joinedload(Prestamo.libro), joinedload(Prestamo.usuario)).filter(
        Prestamo.fecha_devolucion.is_(None)
    ).all()

    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Préstamos', 'url': url_for('prestamos.gestionar_prestamos')}
    ]

    return render_template('gestionar_prestamos.html', prestamos=prestamos, breadcrumbs=breadcrumbs)

