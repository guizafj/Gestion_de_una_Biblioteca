"""Modulo creado para la gestion de libros"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from modules.models_libro import Libro
from modules.forms import AgregarLibroForm, EditarLibroForm
from modules.permissions import requiere_rol
from extensions import db
import logging
import os
import csv
from werkzeug.utils import secure_filename

libros_bp = Blueprint('libros', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Configurar la carpeta de subida
def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@libros_bp.route('/agregar_libro', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def agregar_libro():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Libros', 'url': url_for('libros.gestion_libros')},
        {'name': 'Agregar Libro', 'url': url_for('libros.agregar_libro')}
    ]
    form = AgregarLibroForm()

    if form.validate_on_submit():
        try:
            # Validar el ISBN usando el método de models_libro.py
            isbn = form.isbn.data
            isbn_validado = Libro.validar_isbn(isbn)

            # Convertir y validar los datos del formulario
            cantidad = int(form.cantidad.data)
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser un número entero positivo.")
            
            # Crear un nuevo libro
            nuevo_libro = Libro(
                isbn=isbn_validado,
                titulo=form.titulo.data.strip(),
                autor=form.autor.data.strip(),
                editorial=form.editorial.data.strip(),
                genero=form.genero.data.strip(),
                cantidad=cantidad,
            )
            db.session.add(nuevo_libro)
            db.session.commit()

            flash('Libro agregado exitosamente.', 'success')
            return redirect(url_for('libros.gestion_libros'))

        except ValueError as ve:
            # Manejar errores de validación
            logging.error(f"Error de validación al agregar libro: {str(ve)}")
            flash(str(ve), 'danger')

        except Exception as e:
            # Manejar errores generales
            logging.error(f"Error inesperado al agregar libro: {str(e)}")
            db.session.rollback()
            flash("Ocurrió un error al agregar el libro. Intenta nuevamente.", "danger")

    return render_template('agregar_libro.html', form=form, breadcrumbs=breadcrumbs)

@libros_bp.route('/buscar_libro', methods=['GET', 'POST'])
def buscar_libro():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Buscar Libro', 'url': url_for('libros.buscar_libro')}
    ]
    termino = request.args.get('termino', '').strip()
    libros = []
    if termino:
        libros = Libro.query.filter(
            (Libro.titulo.ilike(f"%{termino}%")) |
            (Libro.autor.ilike(f"%{termino}%")) |
            (Libro.isbn.ilike(f"%{termino}%")) |
            (Libro.genero.ilike(f"%{termino}%")) |
            (Libro.editorial.ilike(f"%{termino}%"))
        ).all()
    return render_template('buscar_libro.html', libros=libros, termino=termino, breadcrumbs=breadcrumbs)

@libros_bp.route('/gestion_libros')
@login_required
@requiere_rol('bibliotecario', 'admin')
def gestion_libros():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Libros', 'url': url_for('libros.gestion_libros')}
    ]
    libros = Libro.query.all()
    return render_template('gestion_libros.html', libros=libros, breadcrumbs=breadcrumbs)

@libros_bp.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def editar_libro(libro_id):
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Libros', 'url': url_for('libros.gestion_libros')},
        {'name': 'Editar Libro', 'url': url_for('libros.editar_libro', libro_id=libro_id)}
    ]
    libro = Libro.query.get_or_404(libro_id)
    form = EditarLibroForm(libro_id=libro.id, obj=libro)
    if form.validate_on_submit():
        libro.isbn = form.isbn.data
        libro.titulo = form.titulo.data
        libro.autor = form.autor.data
        libro.editorial = form.editorial.data
        libro.genero = form.genero.data
        libro.cantidad = form.cantidad.data
        db.session.commit()
        flash('Libro actualizado con éxito.', 'success')
        return redirect(url_for('libros.gestion_libros'))
    return render_template('editar_libro.html', libro=libro, form=form, breadcrumbs=breadcrumbs)

@libros_bp.route('/eliminar_libro/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def eliminar_libro(libro_id):
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Libros', 'url': url_for('libros.gestion_libros')},
        {'name': 'Eliminar Libro', 'url': url_for('libros.eliminar_libro', libro_id=libro_id)}
    ]
    libro = Libro.query.get_or_404(libro_id)
    if request.method == 'POST':
        try:
            logging.info(f"Intentando eliminar el libro: {libro.titulo} (ID: {libro.id})")
            db.session.delete(libro)
            db.session.commit()
            flash(f'Libro "{libro.titulo}" eliminado correctamente.', 'success')
            return redirect(url_for('libros.gestion_libros'))
        except Exception as e:
            db.session.rollback()  # Revertir la transacción fallida
            logging.error(f"Error al eliminar libro: {e}")
            flash("Ocurrió un error al eliminar el libro. Intenta nuevamente.", "danger")
    return render_template('eliminar_libro.html', libro=libro, breadcrumbs=breadcrumbs)

@libros_bp.route('/autores', methods=['GET'])
@login_required
def libros_por_autor():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Autores', 'url': url_for('libros.libros_por_autor')}
    ]
    libros = Libro.query.all()
    data = {}
    for libro in libros:
        if libro.autor not in data:
            data[libro.autor] = []
        data[libro.autor].append({
            'id': libro.id,
            'titulo': libro.titulo,
            'esta_disponible': libro.esta_disponible()  # Incluye el resultado del método
        })
    return render_template('autores.html', data=data, breadcrumbs=breadcrumbs)

@libros_bp.route('/generos', methods=['GET'])
@login_required
def libros_por_genero():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Genero', 'url': url_for('libros.libros_por_genero')}
    ]
    libros = Libro.query.all()
    data = {}
    for libro in libros:
        if libro.genero not in data:
            data[libro.genero] = []
        data[libro.genero].append({
            'id': libro.id,
            'titulo': libro.titulo,
            'esta_disponible': libro.esta_disponible()  # Incluye el resultado del método
        })
    return render_template('generos.html', data=data, breadcrumbs=breadcrumbs)

@libros_bp.route('/titulos', methods=['GET'])
@login_required
def libros_por_titulo():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Titulo', 'url': url_for('libros.libros_por_titulo')}
    ]
    libros = Libro.query.all()
    data = {}
    for libro in libros:
        if libro.titulo not in data:
            data[libro.titulo] = []
        data[libro.titulo].append({
            'id': libro.id,  # Incluye el ID del libro
            'titulo': libro.titulo,
            'autor': libro.autor,  # Incluye el autor del libro
            'disponible': libro.esta_disponible()
        })
    return render_template('titulos.html', data=data, breadcrumbs=breadcrumbs)

@libros_bp.route('/importar_datos', methods=['GET', 'POST'])
@login_required
@requiere_rol('admin')
def importar_datos():
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Gestión de Libros', 'url': url_for('libros.gestion_libros')},
        {'name': 'Importar Datos', 'url': url_for('libros.importar_datos')}
    ]
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            try:
                with open(filepath, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if not row['titulo'] or not row['autor'] or not row['isbn'] or not row['cantidad'] or not row['editorial'] or not row['genero']:
                            raise ValueError("Faltan campos obligatorios en el archivo CSV.")
                        nuevo_libro = Libro(
                            titulo=row['titulo'],
                            autor=row['autor'],
                            isbn=row['isbn'],
                            editorial=row['editorial'],
                            genero=row['genero'],
                            cantidad=int(row['cantidad']),
                        )
                        db.session.add(nuevo_libro)
                    db.session.commit()
                    flash('Datos importados exitosamente.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al importar datos: {e}', 'danger')
            finally:
                os.remove(filepath)
            return redirect(url_for('libros.gestion_libros'))
    return render_template('importar_datos.html', breadcrumbs=breadcrumbs)