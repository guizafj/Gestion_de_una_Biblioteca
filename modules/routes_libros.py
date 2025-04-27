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
    form = AgregarLibroForm()
    if form.validate_on_submit():
        nuevo_libro = Libro(
            isbn=form.isbn.data,
            titulo=form.titulo.data,
            autor=form.autor.data,
            cantidad=form.cantidad.data,
        )
        db.session.add(nuevo_libro)
        db.session.commit()
        flash('Libro agregado exitosamente.', 'success')
        return redirect(url_for('libros.gestion_libros'))
    return render_template('agregar_libro.html', form=form)

@libros_bp.route('/buscar_libro', methods=['GET', 'POST'])
def buscar_libro():
    termino = request.args.get('termino', '').strip()
    libros = []
    if termino:
        libros = Libro.query.filter(
            (Libro.titulo.ilike(f"%{termino}%")) |
            (Libro.autor.ilike(f"%{termino}%")) |
            (Libro.isbn.ilike(f"%{termino}%"))
        ).all()
    return render_template('buscar_libro.html', libros=libros, termino=termino)

@libros_bp.route('/gestion_libros')
@login_required
@requiere_rol('bibliotecario', 'admin')
def gestion_libros():
    libros = Libro.query.all()
    return render_template('gestion_libros.html', libros=libros)

@libros_bp.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def editar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    form = EditarLibroForm(libro_id=libro.id, obj=libro)
    if form.validate_on_submit():
        libro.isbn = form.isbn.data
        libro.titulo = form.titulo.data
        libro.autor = form.autor.data
        libro.cantidad = form.cantidad.data
        db.session.commit()
        flash('Libro actualizado con éxito.', 'success')
        return redirect(url_for('libros.gestion_libros'))
    return render_template('editar_libro.html', libro=libro, form=form)

@libros_bp.route('/eliminar_libro/<int:libro_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario', 'admin')
def eliminar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if request.method == 'POST':
        try:
            db.session.delete(libro)
            db.session.commit()
            flash(f'Libro "{libro.titulo}" eliminado correctamente.', 'success')
            return redirect(url_for('libros.gestion_libros'))
        except Exception as e:
            logging.error(f"Error al eliminar libro: {e}")
            flash("Ocurrió un error al eliminar el libro. Intenta nuevamente.", "danger")
    return render_template('eliminar_libro.html', libro=libro)

@libros_bp.route('/autores', methods=['GET'])
@login_required
def libros_por_autor():
    libros = Libro.query.all()
    data = {}
    for libro in libros:
        if libro.autor not in data:
            data[libro.autor] = []
        data[libro.autor].append({
            'titulo': libro.titulo,
            'disponible': libro.disponible
        })
    return render_template('autores.html', data=data)

@libros_bp.route('/importar_datos', methods=['GET', 'POST'])
@login_required
@requiere_rol('admin')
def importar_datos():
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
                        if not row['titulo'] or not row['autor'] or not row['isbn'] or not row['cantidad']:
                            raise ValueError("Faltan campos obligatorios en el archivo CSV.")
                        nuevo_libro = Libro(
                            titulo=row['titulo'],
                            autor=row['autor'],
                            isbn=row['isbn'],
                            cantidad=int(row['cantidad']),
                            disponible=int(row['cantidad'])
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
    return render_template('importar_datos.html')