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

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5 per minute"]  # Limita a 5 intentos por minuto
)
logging.basicConfig(filename='app.log', level=logging.INFO)

# Decorador personalizado para restringir acceso a bibliotecarios
def bibliotecario_requerido(f):
    """
    Decorador para restringir el acceso a rutas exclusivas de bibliotecarios.
    Si el usuario no es un bibliotecario, se redirige al índice con un mensaje flash.
    """
    @wraps(f) # Esto preserva el nombre y los metadatos de la función original
    def wrapper(*args, **kwargs):
        if not current_user.es_bibliotecario():
            flash('Acceso denegado. Solo los bibliotecarios pueden acceder a esta ruta.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper

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
            try:
                usuario = Usuario(
                    nombre=form.nombre.data,
                    email=form.email.data,
                    rol=form.rol.data
                )
                usuario.set_password(form.contrasena.data)  # Hashea la contraseña
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
                flash('Registro exitoso. Por favor, confirma tu correo electrónico.')
                return redirect(url_for('login'))
            except Exception as e:
                logging.error(f"Error al registrar usuario: {e}")
                flash('Ocurrió un error al registrar el usuario. Intenta nuevamente.', 'danger')
        return render_template('registro.html', form=form)

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
    @bibliotecario_requerido
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
    @bibliotecario_requerido
    def gestion_libros():
        """
        Muestra una lista de libros con opciones para editar o eliminar.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libros = Libro.query.all()
        return render_template('gestion_libros.html', libros=libros) 

    @app.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    @bibliotecario_requerido
    def editar_libro(libro_id):
        """
        Permite editar un libro específico.
        Solo los bibliotecarios pueden acceder a esta ruta.
        """
        libro = Libro.query.get_or_404(libro_id)
        if request.method == 'POST':
            libro.titulo = request.form['titulo']
            libro.autor = request.form['autor']
            libro.isbn = request.form['isbn']
            db.session.commit()
            flash(f'Libro "{libro.titulo}" editado correctamente.', 'success')
            return redirect(url_for('index'))
        return render_template('editar_libro.html', libro=libro)

    @app.route('/eliminar_libro/<int:libro_id>', methods=['GET', 'POST'])
    @login_required
    @bibliotecario_requerido
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
        prestamos = Prestamo.query.options(joinedload.filter_by(usuario_id=current_user.id).all())
        params = {'usuario_id': current_user.id, 'total_prestamos': len(prestamos)}
        query_string = urlencode(params)
        return render_template('historial.html', prestamos=prestamos, query_string=query_string)
    
    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        return render_template('error.html', mensaje="La página solicitada no existe."), 404