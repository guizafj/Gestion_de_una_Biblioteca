from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, mail
from modules.models import Libro, Usuario, Prestamo
from modules.forms import RegistroForm, LoginForm
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask_mail import Message  # Import Message from flask_mail

# Decorador personalizado para restringir acceso a bibliotecarios
def bibliotecario_requerido(f):
    def wrapper(*args, **kwargs):
        if not current_user.es_bibliotecario():
            flash('Solo los bibliotecarios pueden acceder a esta ruta.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper

# Rutas de Autenticación
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()
    if form.validate_on_submit():
        usuario = Usuario(
            nombre=form.nombre.data,
            email=form.email.data,
            contrasena=form.contrasena.data,
            rol=form.rol.data
        )
        db.session.add(usuario)
        db.session.commit()

        # Generar y enviar correo de confirmación
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
    return render_template('registro.html', form=form)

@app.route('/confirmar_email/<token>')
def confirmar_email(token):
    usuario = Usuario.query.filter_by(token_confirmacion=token).first()
    if not usuario:
        flash('El enlace de confirmación es inválido o ha expirado.')
        return redirect(url_for('index'))
    usuario.confirmar_email()
    flash('Correo electrónico confirmado correctamente. Ahora puedes iniciar sesión.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.contrasena == form.contrasena.data:
            if not usuario.email_confirmado:
                flash('Por favor, confirma tu correo electrónico antes de iniciar sesión.')
                return redirect(url_for('index'))
            login_user(usuario)
            flash('Inicio de sesión exitoso.')
            return redirect(url_for('index'))
        flash('Credenciales incorrectas.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.')
    return redirect(url_for('index'))

# Rutas de Libros
@app.route('/')
def index():
    libros = Libro.query.all()
    total_libros = Libro.contar_libros()
    return render_template('index.html', libros=libros, total_libros=total_libros)

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('query', '').strip()
    if not query:
        flash('Por favor, ingresa un término de búsqueda.')
        return redirect(url_for('index'))
    libros = Libro.query.filter(
        (Libro.titulo.ilike(f"%{query}%")) |
        (Libro.autor.ilike(f"%{query}%")) |
        (Libro.isbn == query)
    ).all()
    if not libros:
        flash('No se encontraron resultados para tu búsqueda.')
    return render_template('buscar_libro.html', libros=libros, query=query)

@app.route('/agregar_libro', methods=['GET', 'POST'])
@login_required
@bibliotecario_requerido
def agregar_libro():
    if request.method == 'POST':
        isbn = request.form['isbn'].strip()
        titulo = request.form['titulo'].strip()
        autor = request.form['autor'].strip()

        if not Libro.validar_isbn(isbn):
            flash('El ISBN debe tener 10 o 13 dígitos.')
            return redirect(url_for('agregar_libro'))
        if not Libro.validar_titulo(titulo):
            flash('Ya existe un libro con este título.')
            return redirect(url_for('agregar_libro'))

        libro = Libro(isbn=isbn, titulo=titulo, autor=autor)
        db.session.add(libro)
        db.session.commit()
        flash('Libro agregado correctamente.')
        return redirect(url_for('index'))
    return render_template('agregar_libro.html')

@app.route('/editar_libro_lista')
@login_required
@bibliotecario_requerido
def editar_libro_lista():
    libros = Libro.query.all()
    return render_template('editar_libro_lista.html', libros=libros)

@app.route('/eliminar_libro_lista')
@login_required
@bibliotecario_requerido
def eliminar_libro_lista():
    libros = Libro.query.all()
    return render_template('eliminar_libro_lista.html', libros=libros)

@app.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@bibliotecario_requerido
def editar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if request.method == 'POST':
        libro.titulo = request.form['titulo']
        libro.autor = request.form['autor']
        db.session.commit()
        flash(f'Libro "{libro.titulo}" editado correctamente.')
        return redirect(url_for('index'))
    return render_template('editar_libro.html', libro=libro)

@app.route('/eliminar_libro/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@bibliotecario_requerido
def eliminar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if request.method == 'POST':
        db.session.delete(libro)
        db.session.commit()
        flash(f'Libro "{libro.titulo}" eliminado correctamente.')
        return redirect(url_for('index'))
    return render_template('eliminar_libro.html', libro=libro)

# Rutas de Préstamos
@app.route('/prestar/<int:libro_id>', methods=['GET', 'POST'])
@login_required
def prestar(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if not libro.disponible:
        flash('El libro no está disponible para préstamo.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        prestamo = Prestamo(libro_id=libro.id, usuario_id=current_user.id)
        libro.disponible = False
        db.session.add(prestamo)
        db.session.commit()
        flash(f'Libro "{libro.titulo}" prestado correctamente.')
        return redirect(url_for('index'))
    return render_template('prestar_libro.html', libro=libro)

@app.route('/devolver/<int:libro_id>', methods=['GET', 'POST'])
@login_required
def devolver(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    prestamo = Prestamo.query.filter_by(libro_id=libro.id, fecha_devolucion=None).first()
    if not prestamo:
        flash('Este libro no está prestado actualmente.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        prestamo.fecha_devolucion = datetime.utcnow()
        libro.disponible = True
        db.session.commit()
        flash(f'Libro "{libro.titulo}" devuelto correctamente.')
        return redirect(url_for('index'))
    return render_template('devolver_libro.html', libro=libro)

@app.route('/recordatorios')
@login_required
def recordatorios():
    fecha_limite = datetime.timezone.utc() - timedelta(days=7)
    prestamos_pendientes = Prestamo.query.filter(
        Prestamo.usuario_id == current_user.id,
        Prestamo.fecha_devolucion == None,
        Prestamo.fecha_prestamo < fecha_limite
    ).all()
    return render_template('recordatorios.html', prestamos_pendientes=prestamos_pendientes)

@app.route('/historial')
@login_required
def historial():
    prestamos = Prestamo.query.filter_by(usuario_id=current_user.id).all()
    return render_template('historial.html', prestamos=prestamos)