from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.forms.forms import CrearUsuarioForm
from src.models.models_usuario import Usuario
from src.permissions import requiere_rol
from extensions import db
import logging
from src.models.models_prestamo import Prestamo
from sqlalchemy import exc  # Importa las excepciones de SQLAlchemy
from datetime import datetime, timedelta

usuarios_bp = Blueprint('usuarios', __name__)

# Función auxiliar para validar roles
def validar_rol(nuevo_rol):
    ROLES_VALIDOS = ['usuario', 'bibliotecario', 'admin']
    if nuevo_rol not in ROLES_VALIDOS:
        flash("Rol no válido.", "danger")
        return False
    return True

@usuarios_bp.route('/gestion_usuarios', methods=['GET', 'POST'])
@login_required
@requiere_rol('admin')  # Solo accesible para administradores
def gestion_usuarios():
    """
    Muestra una lista de usuarios y permite al administrador gestionar sus roles.
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Usuarios', 'url': url_for('usuarios.gestion_usuarios')}
    ]

    # Manejo de búsqueda
    termino = request.args.get('termino', '').strip()
    usuarios = Usuario.query
    if termino:
        usuarios = usuarios.filter(
            (Usuario.nombre.ilike(f"%{termino}%")) |
            (Usuario.email.ilike(f"%{termino}%"))
        )
    usuarios = usuarios.all()

    # Manejo de actualización de roles
    if request.method == 'POST':
        try:
            usuario_id = request.form.get('usuario_id')
            nuevo_rol = request.form.get('rol')
            usuario = Usuario.query.get_or_404(usuario_id)

            if not validar_rol(nuevo_rol):
                return redirect(url_for('usuarios.gestion_usuarios'))

            # Actualizar el rol del usuario
            usuario.rol = nuevo_rol
            db.session.commit()
            flash(f"Rol actualizado a '{nuevo_rol}' para {usuario.nombre}.", "success")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al actualizar rol: {e}")
            flash("Ocurrió un error al actualizar el rol. Intenta nuevamente.", "danger")
        return redirect(url_for('usuarios.gestion_usuarios'))

    return render_template('gestionar_usuarios.html', usuarios=usuarios, termino=termino, breadcrumbs=breadcrumbs)


@usuarios_bp.route('/cambiar_rol/<int:usuario_id>', methods=['POST'])
@login_required
@requiere_rol('admin')
def cambiar_rol(usuario_id):
    """
    Cambia el rol de un usuario específico.
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Usuarios', 'url': url_for('usuarios.gestion_usuarios')},
        {'name': 'Cambiar Rol', 'url': url_for('usuarios.cambiar_rol', usuario_id=usuario_id)}
    ]

    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        nuevo_rol = request.form.get('rol')

        if not validar_rol(nuevo_rol):
            return redirect(url_for('usuarios.gestion_usuarios'))

        # Evitar que un admin se quite sus propios privilegios
        if usuario.id == current_user.id and usuario.rol == 'admin':
            flash("No puedes modificar tu propio rol de administrador.", "danger")
            return redirect(url_for('usuarios.gestion_usuarios'))

        usuario.rol = nuevo_rol
        db.session.commit()
        flash(f"Rol actualizado correctamente para {usuario.nombre}.", "success")
    except Exception as e:
        logging.error(f"Error al cambiar rol: {e}")
        flash("Error al cambiar el rol.", "danger")
        db.session.rollback()

    return redirect(url_for('usuarios.gestion_usuarios'))



@usuarios_bp.route('/eliminar_usuario/<int:usuario_id>', methods=['POST'])
@login_required
@requiere_rol('admin')  # Solo accesible para administradores
def eliminar_usuario(usuario_id):
    """
    Elimina un usuario específico si no tiene préstamos activos.
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Usuarios', 'url': url_for('usuarios.gestion_usuarios')},
        {'name': 'Eliminar Usuario', 'url': url_for('usuarios.eliminar_usuario', usuario_id=usuario_id)},
    ]

    try:
        usuario = Usuario.query.get_or_404(usuario_id)

        # Manejar las reservas asociadas 
        for reserva in usuario.reservas:
            db.session.delete(reserva)

        # Evitar que un administrador se elimine a sí mismo
        if usuario.id == current_user.id:
            flash("No puedes eliminar tu propia cuenta.", "danger")
            return redirect(url_for('usuarios.gestion_usuarios'))

        # Verificar si el usuario tiene préstamos activos
        prestamos_activos = Prestamo.query.filter_by(usuario_id=usuario.id, fecha_devolucion=None).count()
        if prestamos_activos > 0:
            flash(
                f"No se puede eliminar al usuario {usuario.nombre} porque tiene {prestamos_activos} préstamo(s) activo(s) sin devolver.",
                "warning",
            )
            return redirect(url_for('usuarios.gestion_usuarios'))

        # Eliminar el usuario (las reservas se eliminan automáticamente por CASCADE)
        db.session.delete(usuario)
        db.session.commit()
        flash(f"Usuario {usuario.nombre} eliminado correctamente.", "success")

    except exc.SQLAlchemyError as e:  # Captura excepciones de SQLAlchemy
        db.session.rollback()  # ¡Asegúrate de revertir la sesión aquí!
        logging.error(f"Error al eliminar usuario {usuario.id}: {e}", exc_info=True)  # Registrar la traza completa
        flash(
            "Ocurrió un error al intentar eliminar el usuario. Por favor, inténtalo de nuevo.",
            "danger",
        )

    return redirect(url_for('usuarios.gestion_usuarios'))

@usuarios_bp.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
@requiere_rol('admin')  # Solo accesible para administradores
def crear_usuario():
    """
    Crea un nuevo usuario.
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Crear Usuario', 'url': url_for('usuarios.crear_usuario')}
    ]

    form = CrearUsuarioForm()
    if form.validate_on_submit():
        # Verificar si el correo ya está registrado
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('El correo electrónico ya está registrado. Por favor, usa otro.', 'danger')
            return render_template('crear_usuario.html', form=form)

        try:
            nuevo_usuario = Usuario(
                nombre=form.nombre.data,
                email=form.email.data,
                rol=form.rol.data
            )
            nuevo_usuario.set_password(form.contrasena.data) 
            # Generar token de confirmación
            token = nuevo_usuario.generar_token_confirmacion()
            nuevo_usuario.token_confirmacion = token
            nuevo_usuario.token_expiracion = datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas

            db.session.add(nuevo_usuario)
            db.session.commit()

            # Enviar correo de confirmación
            try:
                Usuario.enviar_correo(
                    email=nuevo_usuario.email,
                    token=token,
                    ruta="auth.confirmar_email",  # Nombre completo del endpoint
                    asunto="Confirmación de correo electrónico",
                    mensaje="Para confirmar tu correo electrónico, haz clic en el siguiente enlace:",
                    plantilla="confirmar_email.html"  # Nombre del template
                )
            except Exception as e:
                logging.error(f"Error al enviar el correo de confirmación: {e}")
                flash('No se pudo enviar el correo de confirmación. Por favor, intenta nuevamente.', 'danger')
                return redirect(url_for('usuarios.gestion_usuarios'))

            flash('Usuario registrado exitosamente, confirma tu correo electrónico.', 'success')
            flash(f"Usuario {nuevo_usuario.nombre} creado correctamente.", "success")
            return redirect(url_for('usuarios.gestion_usuarios'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al crear usuario: {e}")
            flash('Ocurrió un error al crear el usuario. Por favor, intenta nuevamente.', 'danger')

    return render_template('crear_usuario.html', form=form)


@usuarios_bp.route('/auth/recuperar_cuenta', methods=['POST'])
def recuperar_cuenta():
    email = request.form.get('email')
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario:
        token = generar_token(usuario)
        try:
            usuario.enviar_correo('recuperar_cuenta.html', token=token)
            flash('Correo de recuperación enviado', 'success')
        except Exception as e:
            app.logger.error(f"Error en recuperación de cuenta: {e}")
            flash('Error al enviar el correo de recuperación', 'danger')
    else:
        flash('Usuario no encontrado', 'warning')
    return redirect(url_for('auth.recuperar_cuenta'))