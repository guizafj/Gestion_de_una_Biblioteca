ROLES_PERMITIDOS = {
    'admin': ['gestionar_usuarios', 'cambiar_rol'],
    'bibliotecario': ['agregar_libro', 'editar_libro', 'eliminar_libro', 'gestion_libros'],
    'usuario': ['prestar', 'devolver', 'historial', 'recordatorios']
}

from flask import render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from modules.models import Libro, Usuario, Prestamo
from modules.forms import RegistroForm, LoginForm, AgregarLibroForm, EditarLibroForm  # Añadir AgregarLibroForm y EditarLibroForm
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from flask_mail import Message
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from sqlalchemy.orm import joinedload
import re
from sqlalchemy.exc import IntegrityError
import os 
import urllib.parse


# Configuración del logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# Decorador personalizado para restringir acceso por rol
def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder.', 'warning')
                return redirect(url_for('login'))
                
            if not any(current_user.tiene_rol(rol) for rol in roles):
                logging.warning(f"Intento de acceso no autorizado: {current_user.email}")
                flash('No tiene permisos para acceder a esta página.', 'danger')
                return redirect(url_for('index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Función para registrar rutas
def register_routes(app, db, mail):
    """
    Registra todas las rutas de la aplicación.
    Esta función permite evitar importaciones circulares al usar el patrón "App Factory".
    """
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


    @app.route('/')
    def index():
        """
        Página principal de la aplicación.
        Muestra una lista de libros disponibles y el total de libros en la biblioteca.
        """
        libros = Libro.query.all()
        total_libros = Libro.contar_libros()
        return render_template('index.html', libros=libros, total_libros=total_libros)
    
    @app.route('/registro', methods=['GET', 'POST'])
    def registro():
        form = RegistroForm()
        if form.validate_on_submit():
            try:
                email = form.email.data.strip()
                
                # Validar formato del correo
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(pattern, email):
                    flash("Por favor, ingresa un correo electrónico válido.", "warning")
                    return redirect(url_for('registro'))

                # Verificar si el correo ya está registrado
                usuario_existente = Usuario.query.filter_by(email=email).first()
                if usuario_existente:
                    flash("El correo electrónico ya está registrado.", "danger")
                    return redirect(url_for('registro'))

                # Validar contraseña
                if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', form.contrasena.data):
                    flash("La contraseña debe tener al menos 8 caracteres, incluyendo letras y números.", "warning")
                    return redirect(url_for('registro'))

                usuario = Usuario(
                    nombre=form.nombre.data.strip(),
                    email=email,  # No es necesario codificar/decodificar aquí
                    rol=form.rol.data
                )
                usuario.set_password(form.contrasena.data)
                db.session.add(usuario)
                db.session.commit()

                # Generar token y enviar correo
                token = usuario.generar_token_confirmacion()
                try:
                    enlace = url_for('confirmar_email', token=token, _external=True)
                    
                    Usuario.enviar_correo(
                        email=usuario.email,
                        token=token,
                        ruta="confirmar_email",
                        asunto="Confirma tu correo electrónico",
                        mensaje="Haz clic en el siguiente enlace para confirmar tu correo:"
                    )
                    flash("Registro exitoso. Por favor, confirma tu correo electrónico.", "success")
                    return redirect(url_for('login'))
                except Exception as e:
                    logging.error(f"Error al enviar correo: {e}")
                    flash("Ocurrió un error al enviar el correo. Intenta nuevamente.", "danger")
                    db.session.rollback()
                    return render_template('registro.html', form=form)

            except Exception as e:
                logging.error(f"Error al registrar usuario: {e}")
                flash("Ocurrió un error inesperado. Intenta nuevamente.", "danger")
                db.session.rollback()
                
        return render_template('registro.html', form=form)


    @app.route('/confirmar_email/<token>')
    def confirmar_email(token):
        """
        Confirma el correo electrónico del usuario usando el token proporcionado.
        """
        try:
            usuario = Usuario.query.filter_by(token_confirmacion=token).first()
            if not usuario:
                return render_template('confirmar_email.html', error='El enlace de confirmación no es válido.')
            
            if datetime.utcnow() > usuario.token_expiracion:
                return render_template('confirmar_email.html', error='El enlace de confirmación ha expirado.')
            
            usuario.email_confirmado = True
            usuario.token_confirmacion = None
            usuario.token_expiracion = None
            db.session.commit()
            
            flash('Tu correo electrónico ha sido confirmado correctamente.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logging.error(f"Error al confirmar el correo: {e}")
            return render_template('confirmar_email.html', 
                                 error='Ha ocurrido un error al confirmar tu correo electrónico.')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            usuario = Usuario.query.filter_by(email=form.email.data).first()
            if usuario:
                if usuario.esta_bloqueada():
                    flash('Tu cuenta está bloqueada temporalmente. Intenta más tarde.', 'danger')
                    return redirect(url_for('login'))

                if usuario.check_password(form.contrasena.data):
                    usuario.resetear_intentos_fallidos()
                    login_user(usuario)
                    flash('Inicio de sesión exitoso.', 'success')
                    return redirect(url_for('index'))
                else:
                    usuario.intentos_fallidos += 1
                    db.session.commit()
                    if usuario.limitador_inicio():
                        flash('Demasiados intentos fallidos. Tu cuenta ha sido bloqueada temporalmente.', 'danger')
                    else:
                        flash('Credenciales incorrectas. Intenta nuevamente.', 'warning')
            else:
                flash('No se encontró una cuenta con ese correo electrónico.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        """
        Cierra la sesión del usuario actual.
        Redirige al índice después de cerrar la sesión.
        """
        logout_user()
        flash('Sesión cerrada correctamente.', 'info')
        return redirect(url_for('index'))

    @app.route('/agregar_libro', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('bibliotecario', 'admin')  # Solo accesible para bibliotecarios y administradores
    def agregar_libro():
        """
        Permite agregar un nuevo libro a la biblioteca.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        form = AgregarLibroForm()
        if form.validate_on_submit():
            try:
                isbn = form.isbn.data.strip()
                titulo = form.titulo.data.strip()
                autor = form.autor.data.strip()

                # Validar ISBN (10 o 13 dígitos)
                if not Libro.validar_isbn(isbn):
                    flash("El ISBN debe tener 10 o 13 dígitos.", "danger")
                    return redirect(url_for('agregar_libro'))

                # Validar que el título no esté duplicado
                if not Libro.validar_titulo(titulo):
                    flash("Ya existe un libro con este título.", "danger")
                    return redirect(url_for('agregar_libro'))

                # Crear el nuevo libro
                libro = Libro(
                    isbn=isbn,
                    titulo=titulo,
                    autor=autor
                )
                db.session.add(libro)
                db.session.commit()

                flash("Libro agregado correctamente.", "success")
                return redirect(url_for('index'))
            except Exception as e:
                logging.error(f"Error al agregar libro: {e}")
                flash("Ocurrió un error al agregar el libro. Intenta nuevamente.", "danger")
        return render_template('agregar_libro.html', form=form)


    @app.route('/gestion_libros')
    @login_required
    @requiere_rol('bibliotecario', 'admin')  # Solo accesible para bibliotecarios y administradores
    def gestion_libros():
        """
        Muestra una lista de libros con opciones para editar o eliminar.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libros = Libro.query.all()
        return render_template('gestion_libros.html', libros=libros)


    @app.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('bibliotecario', 'admin')  # Solo accesible para bibliotecarios y administradores
    def editar_libro(libro_id):
        """
        Permite editar un libro específico.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libro = Libro.query.get_or_404(libro_id)
        form = EditarLibroForm(obj=libro)  # Inicializar el formulario con los datos del libro

        if form.validate_on_submit():
            try:
                form.populate_obj(libro)  # Actualizar el objeto libro con los datos del formulario
                db.session.commit()
                flash(f'Libro "{libro.titulo}" editado correctamente.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                logging.error(f"Error al editar libro: {e}")
                flash("Ocurrió un error al editar el libro. Intenta nuevamente.", "danger")

        return render_template('editar_libro.html', form=form, libro=libro)  # Pasar el formulario al template


    @app.route('/eliminar_libro/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('bibliotecario', 'admin')  # Solo accesible para bibliotecarios y administradores
    def eliminar_libro(libro_id):
        """
        Permite eliminar un libro específico.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libro = Libro.query.get_or_404(libro_id)

        if request.method == 'POST':
            try:
                db.session.delete(libro)
                db.session.commit()
                flash(f'Libro "{libro.titulo}" eliminado correctamente.', 'success')
                return redirect(url_for('gestion_libros'))  # Redirigir a la página de gestión de libros
            except Exception as e:
                logging.error(f"Error al eliminar libro: {e}")
                flash("Ocurrió un error al eliminar el libro. Intenta nuevamente.", "danger")

        return render_template('eliminar_libro.html', libro=libro)


    @app.route('/prestar/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    def prestar(libro_id):
        """
        Permite prestar un libro a un usuario.
        El libro debe estar disponible para préstamo.
        """
        libro = Libro.query.get_or_404(libro_id)

        if not libro.disponible:
            flash('El libro no está disponible para préstamo.', 'warning')
            return redirect(url_for('index'))

        if request.method == 'POST':
            try:
                prestamo = Prestamo(
                    libro_id=libro.id,
                    usuario_id=current_user.id
                )
                libro.disponible = False
                db.session.add(prestamo)
                db.session.commit()

                flash(f'Libro "{libro.titulo}" prestado correctamente.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                logging.error(f"Error al prestar libro: {e}")
                flash("Ocurrió un error al prestar el libro. Intenta nuevamente.", "danger")

        return render_template('prestar_libro.html', libro=libro)


    @app.route('/devolver/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    def devolver(libro_id):
        """
        Permite devolver un libro prestado.
        Actualiza el estado del libro y registra la fecha de devolución.
        """
        libro = Libro.query.get_or_404(libro_id)
        prestamo = Prestamo.query.filter_by(libro_id=libro.id, fecha_devolucion=None).first()

        if not prestamo:
            flash('Este libro no está prestado actualmente.', 'warning')
            return redirect(url_for('index'))

        if request.method == 'POST':
            try:
                prestamo.fecha_devolucion = datetime.now(timezone.utc)
                libro.disponible = True
                db.session.commit()

                flash(f'Libro "{libro.titulo}" devuelto correctamente.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                logging.error(f"Error al devolver libro: {e}")
                flash("Ocurrió un error al devolver el libro. Intenta nuevamente.", "danger")

        return render_template('devolver_libro.html', libro=libro)
    
    @app.route('/gestion_usuarios', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('admin')  # Solo accesible para administradores
    def gestion_usuarios():
        """
        Muestra una lista de usuarios y permite al administrador gestionar sus roles.
        Solo los administradores pueden acceder a esta ruta.
        """
        if request.method == 'POST':
            try:
                usuario_id = request.form.get('usuario_id')
                nuevo_rol = request.form.get('rol')
                usuario = Usuario.query.get_or_404(usuario_id)

                # Validar que el rol sea válido
                if nuevo_rol not in ['usuario', 'bibliotecario', 'admin']:
                    flash("Rol no válido.", "danger")
                    return redirect(url_for('gestion_usuarios'))

                # Actualizar el rol del usuario
                if nuevo_rol != usuario.rol:  # Validar si el nuevo rol es diferente al rol actual
                    usuario.rol = nuevo_rol
                    db.session.commit()
                    flash(f"Rol actualizado a '{nuevo_rol}' para {usuario.nombre}.", "success")
                else:
                    flash("El usuario ya tiene ese rol.", "info")
                return redirect(url_for('gestion_usuarios'))
            except Exception as e:
                logging.error(f"Error al actualizar rol: {e}")
                flash("Ocurrió un error al actualizar el rol. Intenta nuevamente.", "danger")

        # Mostrar la lista de usuarios
        usuarios = Usuario.query.all()
        return render_template('gestion_usuarios.html', usuarios=usuarios)


    @app.route('/recordatorios')
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

            return render_template('recordatorios.html', prestamos_pendientes=prestamos_pendientes)
        except Exception as e:
            logging.error(f"Error al cargar recordatorios: {e}")
            flash("Ocurrió un error al cargar los recordatorios. Intenta nuevamente.", "danger")
            return redirect(url_for('index'))


    @app.route('/historial')
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
            return render_template('historial.html', prestamos=prestamos, query_string=query_string)
        except Exception as e:
            logging.error(f"Error al cargar historial: {e}")
            flash("Ocurrió un error al cargar el historial. Intenta nuevamente.", "danger")
            return redirect(url_for('index'))
        
    @app.route('/recuperar_cuenta', methods=['GET', 'POST'])
    def recuperar_cuenta():
        """
        Permite a los usuarios solicitar un enlace para restablecer su contraseña.
        """
        if request.method == 'POST':
            try:
                email = request.form.get('email').strip()

                # Validar formato del correo electrónico
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not email or not re.match(pattern, email):
                    flash("Por favor, ingresa un correo electrónico válido.", "warning")
                    return redirect(url_for('recuperar_cuenta'))

                usuario = Usuario.query.filter_by(email=email).first()
                if not usuario:
                    flash("El correo electrónico no está registrado.", "warning")
                    return redirect(url_for('recuperar_cuenta'))

                # Generar token y enviar correo
                token = usuario.generar_token_confirmacion()
                enlace = url_for('restablecer_contrasena', token=token, _external=True)

                Usuario.enviar_correo(
                    email=usuario.email,
                    token=token,
                    ruta="restablecer_contrasena",
                    asunto="Recuperación de contraseña",
                    mensaje="Para restablecer tu contraseña, haz clic en el siguiente enlace:"
                )
                flash("Se ha enviado un enlace de recuperación a tu correo electrónico.", "info")
                return redirect(url_for('login'))

            except Exception as e:
                logging.error(f"Error en recuperación de cuenta: {e}")
                flash("Ocurrió un error. Por favor, intenta nuevamente.", "danger")

        return render_template('recuperar_cuenta.html')


    @app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
    def restablecer_contrasena(token):
        """
        Permite a los usuarios restablecer su contraseña usando un token válido.
        """
        usuario = Usuario.query.filter_by(token_confirmacion=token).first()

        # Verificar si el token es válido
        if not usuario or datetime.utcnow() > usuario.token_expiracion:
            flash("El enlace de recuperación no es válido o ha expirado.", "danger")
            return redirect(url_for('recuperar_cuenta'))

        if request.method == 'POST':
            nueva_contrasena = request.form.get('contrasena').strip()

            # Validar la nueva contraseña
            if not nueva_contrasena or len(nueva_contrasena) < 8:
                flash("La contraseña debe tener al menos 8 caracteres.", "warning")
                return redirect(url_for('restablecer_contrasena', token=token))

            try:
                # Actualizar la contraseña del usuario
                usuario.set_password(nueva_contrasena)
                usuario.token_confirmacion = None  # Eliminar el token después de usarlo
                usuario.token_expiracion = None
                db.session.commit()

                flash("Tu contraseña ha sido restablecida con éxito. Ahora puedes iniciar sesión.", "success")
                return redirect(url_for('login'))
            except Exception as e:
                logging.error(f"Error al restablecer la contraseña: {e}")
                flash("Ocurrió un error al restablecer tu contraseña. Intenta nuevamente más tarde.", "danger")

        return render_template('restablecer_contrasena.html', token=token)


    @app.route('/gestionar_usuarios', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('admin')
    def gestionar_usuarios():
        """
        Gestiona usuarios y sus roles.
        Solo accesible para administradores.
        """
        if request.method == 'POST':
            try:
                usuario_id = request.form.get('usuario_id')
                nuevo_rol = request.form.get('rol')
                usuario = Usuario.query.get_or_404(usuario_id)

                if nuevo_rol not in Usuario.ROLES:
                    flash("Rol no válido.", "danger")
                    return redirect(url_for('gestionar_usuarios'))

                usuario.rol = nuevo_rol
                db.session.commit()
                flash(f"Rol actualizado a '{nuevo_rol}' para {usuario.nombre}.", "success")
                
            except Exception as e:
                logging.error(f"Error al actualizar rol: {e}")
                flash("Error al actualizar rol.", "danger")
                db.session.rollback()

        usuarios = Usuario.query.all()
        return render_template('gestionar_usuarios.html', usuarios=usuarios)

    @app.route('/cambiar_rol/<int:usuario_id>', methods=['POST'])
    @login_required
    @requiere_rol('admin')
    def cambiar_rol(usuario_id):
        """
        Cambia el rol de un usuario específico.
        Args:
            usuario_id (int): ID del usuario a modificar
        """
        try:
            usuario = Usuario.query.get_or_404(usuario_id)
            nuevo_rol = request.form.get('rol')
            
            if nuevo_rol not in Usuario.ROLES:
                flash("Rol no válido.", "danger")
                return redirect(url_for('gestionar_usuarios'))
            
            # Evitar que un admin se quite sus propios privilegios
            if usuario.id == current_user.id and usuario.es_admin():
                flash("No puedes modificar tu propio rol de administrador.", "danger")
                return redirect(url_for('gestionar_usuarios'))
                
            usuario.rol = nuevo_rol
            db.session.commit()
            flash(f"Rol actualizado correctamente para {usuario.nombre}.", "success")
            
        except Exception as e:
            logging.error(f"Error al cambiar rol: {e}")
            flash("Error al cambiar el rol.", "danger")
            db.session.rollback()
            
        return redirect(url_for('gestionar_usuarios'))

    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        """
        Maneja errores 404 (página no encontrada).
        """
        return render_template('error.html', mensaje="La página solicitada no existe."), 404


    @app.errorhandler(500)
    def error_interno_servidor(error):
        """
        Maneja errores 500 (errores internos del servidor).
        """
        logging.error(f"Error interno del servidor: {error}")
        return render_template('error.html', mensaje="Ha ocurrido un error inesperado. Por favor, intenta nuevamente más tarde."), 500