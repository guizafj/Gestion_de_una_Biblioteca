from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from modules.models_usuario import Usuario
from modules.permissions import requiere_rol
from extensions import db
import logging

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

    return render_template('gestionar_usuarios.html', usuarios=usuarios, termino=termino)

@usuarios_bp.route('/cambiar_rol/<int:usuario_id>', methods=['POST'])
@login_required
@requiere_rol('admin')
def cambiar_rol(usuario_id):
    """
    Cambia el rol de un usuario específico.
    """
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