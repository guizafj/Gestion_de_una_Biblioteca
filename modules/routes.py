from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from modules.models import Libro, Usuario, Prestamo
from modules.forms import RegistroForm, LoginForm, AgregarLibroForm
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode  # Para construir cadenas de consulta
from flask_mail import Message  # Para enviar correos electrónicos
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from sqlalchemy.orm import joinedload

# Configuración del límite de solicitudes
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5 per minute"]  # Limita a 5 intentos por minuto
)

# Configuración del logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# Decorador personalizado para restringir acceso por rol
def requiere_rol(*roles):
    """
    Decorador para restringir el acceso a usuarios con roles específicos.
    Si el usuario no tiene el rol requerido, se redirige al índice con un mensaje flash.
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Debes iniciar sesión para acceder a esta página.", "warning")
                return redirect(url_for('login'))
            if current_user.rol not in roles:
                flash("Acceso denegado. No tienes permiso para acceder a esta página.", "danger")
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorador

# Función para registrar rutas
def register_routes(app, db, mail):
    """
    Registra todas las rutas de la aplicación.
    Esta función permite evitar importaciones circulares al usar el patrón "App Factory".
    """

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
            # Obtener los datos del formulario
            email = form.email.data.strip()  # Asegúrate de eliminar espacios en blanco
            nombre = form.nombre.data.strip()
            contrasena = form.contrasena.data

            # Verificar si el correo ya está registrado
            if Usuario.query.filter_by(email=email).first():
                flash("El correo electrónico ya está registrado. ¿Olvidaste tu contraseña?", "warning")
                return redirect(url_for('recuperar_cuenta'))  # Redirigir a la página de recuperación de cuenta

            # Crear un nuevo usuario
            try:
                usuario = Usuario(
                    nombre=nombre,
                    email=email,
                    rol=form.rol.data
                )
                usuario.set_password(contrasena)  # Hashea la contraseña
                db.session.add(usuario)
                db.session.commit()

                # Generar token de confirmación y enviar correo
                token = usuario.generar_token_confirmacion()
                confirm_url = url_for('confirmar_email', token=token, _external=True)
                msg = Message(
                    subject="Confirma tu correo electrónico",
                    recipients=[usuario.email],
                    body=f"Haz clic en el siguiente enlace para confirmar tu correo: {confirm_url}"
                )
                mail.send(msg)
                flash('Registro exitoso. Por favor, confirma tu correo electrónico.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                logging.error(f"Error al registrar usuario: {e}")
                flash('Ocurrió un error al registrar el usuario. Intenta nuevamente.', 'danger')

    @app.route('/confirmar_email/<token>')
    def confirmar_email(token):
        """
        Confirma el correo electrónico del usuario usando el token proporcionado.
        Si el token es válido, se actualiza el estado del usuario.
        """
        try:
            usuario = Usuario.query.filter_by(token_confirmacion=token).first()
            if not usuario or datetime.utcnow() > usuario.token_expiracion:
                flash('El enlace de confirmación es inválido o ha expirado.', 'warning')
                return redirect(url_for('index'))
            usuario.confirmar_email()
            flash('Correo electrónico confirmado correctamente. Ahora puedes iniciar sesión.', 'success')
        except Exception as e:
            logging.error(f"Error al confirmar el correo: {e}")
            flash('Ocurrió un error al confirmar el correo electrónico.', 'danger')
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute")  # Aplica el límite a esta ruta
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            usuario = Usuario.query.filter_by(email=form.email.data).first()
            if usuario:
                # Verificar si la cuenta está bloqueada
                if usuario.esta_bloqueada():
                    flash('Tu cuenta está bloqueada. Inténtalo más tarde.', 'danger')
                    logging.warning(f"Intento de inicio de sesión en cuenta bloqueada: {form.email.data}")
                    return redirect(url_for('login'))
                
                  # Verificar si el correo está confirmado
                if not usuario.email_confirmado:
                    flash('Por favor, confirma tu correo electrónico antes de iniciar sesión.', 'info')
                    return redirect(url_for('index'))

                # Verificar la contraseña
                if usuario.check_password(form.contrasena.data):
                    if not usuario.email_confirmado:
                        logging.warning(f"Intento de inicio de sesión sin confirmar: {form.email.data}")
                        flash('Por favor, confirma tu correo electrónico antes de iniciar sesión.', 'info')
                        return redirect(url_for('index'))

                    # Restablecer intentos fallidos al iniciar sesión correctamente
                    usuario.resetear_intentos_fallidos()
                    login_user(usuario)
                    logging.info(f"Inicio de sesión exitoso: {form.email.data}")
                    flash('Inicio de sesión exitoso.', 'success')
                    return redirect(url_for('index'))

                # Incrementar intentos fallidos si la contraseña es incorrecta
                usuario.intentos_fallidos += 1
                db.session.commit()
                if usuario.intentos_fallidos >= 5:  # Límite de intentos fallidos
                    usuario.bloquear_cuenta()
                    flash('Demasiados intentos fallidos. Tu cuenta ha sido bloqueada temporalmente.', 'danger')
                    logging.warning(f"Cuenta bloqueada: {form.email.data}")
                    return redirect(url_for('login'))

            logging.warning(f"Fallo en inicio de sesión: {form.email.data}")
            flash('Credenciales incorrectas.', 'danger')
        return render_template('login.html', form=form)
    
    @app.route('/recuperar_cuenta', methods=['GET', 'POST'])
    def recuperar_cuenta():
        """
        Permite a los usuarios solicitar un enlace para restablecer su contraseña.
        """
        if request.method == 'POST':
            email = request.form.get('email').strip()

            # Validar formato del correo
            if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                flash("Por favor, ingresa un correo electrónico válido.", "warning")
                return redirect(url_for('recuperar_cuenta'))

            # Verificar si el correo está registrado
            usuario = Usuario.query.filter_by(email=email).first()
            if not usuario:
                flash("El correo electrónico no está registrado.", "warning")
                return redirect(url_for('recuperar_cuenta'))

            # Generar un token de recuperación
            token = usuario.generar_token_confirmacion()

            # Enviar un correo con el enlace de recuperación
            try:
                Usuario.enviar_correo(
                    email=usuario.email,
                    token=token,
                    ruta="restablecer_contrasena",
                    asunto="Recuperación de contraseña",
                    mensaje="Para restablecer tu contraseña, haz clic en el siguiente enlace:"
                )
                flash("Se ha enviado un enlace de recuperación a tu correo electrónico.", "info")
            except Exception as e:
                logging.error(f"Error al enviar el correo de recuperación: {e}")
                flash("Ocurrió un error al enviar el correo. Intenta nuevamente más tarde.", "danger")

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

    @app.route('/gestion_usuarios', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('admin')
    def gestion_usuarios():
        """
        Muestra una lista de usuarios y permite al administrador gestionar sus roles.
        """
        if request.method == 'POST':
            # Procesar el cambio de rol
            usuario_id = request.form.get('usuario_id')
            nuevo_rol = request.form.get('rol')
            usuario = Usuario.query.get_or_404(usuario_id)
            if nuevo_rol in ['usuario', 'bibliotecario', 'admin']:
                usuario.rol = nuevo_rol
                db.session.commit()
                flash(f"Rol actualizado a '{nuevo_rol}' para el usuario {usuario.nombre}.", 'success')
            else:
                flash("Rol no válido.", 'danger')
            return redirect(url_for('gestion_usuarios'))

        # Mostrar la lista de usuarios
        usuarios = Usuario.query.all()
        return render_template('gestion_usuarios.html', usuarios=usuarios)

    @app.route('/buscar', methods=['GET'])
    def buscar():
        """
        Permite buscar libros por título, autor o ISBN.
        Muestra los resultados de la búsqueda o un mensaje si no hay coincidencias.
        """
        query = request.args.get('query', '').strip()
        if not query:
            flash('Por favor, ingresa un término de búsqueda.', 'warning')
            return redirect(url_for('index'))

        libros = Libro.query.filter(
            (Libro.titulo.ilike(f"%{query}%")) |
            (Libro.autor.ilike(f"%{query}%")) |
            (Libro.isbn == query)
        ).all()

        if not libros:
            flash('No se encontraron resultados para tu búsqueda.', 'info')

        params = {'query': query}
        query_string = urlencode(params)
        return render_template('buscar_libro.html', libros=libros, query=query, query_string=query_string)

    @app.route('/agregar_libro', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('bibliotecario', 'admin')
    def agregar_libro():
        """
        Permite agregar un nuevo libro a la biblioteca.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        form = AgregarLibroForm()
        if form.validate_on_submit():
            libro = Libro(
                isbn=form.isbn.data.strip(),
                titulo=form.titulo.data.strip(),
                autor=form.autor.data.strip()
            )
            db.session.add(libro)
            db.session.commit()
            flash('Libro agregado correctamente.', 'success')
            return redirect(url_for('index'))
        return render_template('agregar_libro.html', form=form)

    @app.route('/gestion_libros')
    @login_required
    @requiere_rol('bibliotecario', 'admin')
    def gestion_libros():
        """
        Muestra una lista de libros con opciones para editar o eliminar.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libros = Libro.query.all()
        return render_template('gestion_libros.html', libros=libros)

    @app.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('bibliotecario', 'admin')
    def editar_libro(libro_id):
        """
        Permite editar un libro específico.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libro = Libro.query.get_or_404(libro_id)
        if request.method == 'POST':
            libro.titulo = request.form['titulo'].strip()
            libro.autor = request.form['autor'].strip()
            libro.isbn = request.form['isbn'].strip()
            db.session.commit()
            flash(f'Libro "{libro.titulo}" editado correctamente.', 'success')
            return redirect(url_for('index'))
        return render_template('editar_libro.html', libro=libro)

    @app.route('/eliminar_libro/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    @requiere_rol('bibliotecario', 'admin')
    def eliminar_libro(libro_id):
        """
        Permite eliminar un libro específico.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libro = Libro.query.get_or_404(libro_id)
        if request.method == 'POST':
            db.session.delete(libro)
            db.session.commit()
            flash(f'Libro "{libro.titulo}" eliminado correctamente.', 'success')
            return redirect(url_for('index'))
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
            prestamo = Prestamo(libro_id=libro.id, usuario_id=current_user.id)
            libro.disponible = False
            db.session.add(prestamo)
            db.session.commit()
            flash(f'Libro "{libro.titulo}" prestado correctamente.', 'success')
            return redirect(url_for('index'))
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
            prestamo.fecha_devolucion = datetime.now(timezone.utc)
            libro.disponible = True
            db.session.commit()
            flash(f'Libro "{libro.titulo}" devuelto correctamente.', 'success')
            return redirect(url_for('index'))
        return render_template('devolver_libro.html', libro=libro)

    @app.route('/recordatorios')
    @login_required
    def recordatorios():
        """
        Muestra recordatorios de préstamos pendientes.
        Incluye préstamos con más de 7 días sin devolución.
        """
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)
        prestamos_pendientes = Prestamo.query.options(joinedload(Prestamo.libro)).filter(
            Prestamo.usuario_id == current_user.id,
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_prestamo < fecha_limite
        ).all()

        params = {'usuario_id': current_user.id, 'pendientes': len(prestamos_pendientes)}
        query_string = urlencode(params)
        return render_template('recordatorios.html', prestamos_pendientes=prestamos_pendientes, query_string=query_string)

    @app.route('/historial')
    @login_required
    def historial():
        """
        Muestra el historial de préstamos del usuario actual.
        """
        prestamos = Prestamo.query.options(joinedload(Prestamo.libro)).filter_by(usuario_id=current_user.id).all()
        params = {'usuario_id': current_user.id, 'total_prestamos': len(prestamos)}
        query_string = urlencode(params)
        return render_template('historial.html', prestamos=prestamos, query_string=query_string)

    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        return render_template('error.html', mensaje="La página solicitada no existe."), 404