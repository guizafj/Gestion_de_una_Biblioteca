"""Modulo definido para las rutas generales."""
from flask import Blueprint, send_from_directory, render_template, url_for
from src.models.models_libro import Libro  # Importar la clase Libro
import os
import logging

# Crear el Blueprint para rutas generales
generales_bp = Blueprint('generales', __name__)

@generales_bp.route('/favicon.ico')
def favicon():
    """
    Sirve el favicon de la aplicación.
    """
    return send_from_directory(
        os.path.join(os.getcwd(), 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@generales_bp.route('/')
def index():
    """
    Página principal de la aplicación.
    Muestra una lista de libros disponibles y el total de libros en la biblioteca.
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')}
    ]
    libros = Libro.query.all()
    libros_data = [
        {
            'id': libro.id,
            'titulo': libro.titulo,
            'autor': libro.autor,
            'esta_disponible': libro.esta_disponible()  # Incluye el resultado del método
        }
        for libro in libros
    ]
    total_libros = Libro.contar_libros()
    return render_template('index.html', libros=libros_data, total_libros=total_libros, breadcrumbs=breadcrumbs)


@generales_bp.app_errorhandler(404)
def pagina_no_encontrada(error):
    """
    Maneja errores 404 (página no encontrada).
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Error 404', 'url': '#'}
    ]
    return render_template('error.html', mensaje="La página solicitada no existe.", breadcrumbs=breadcrumbs), 404


@generales_bp.app_errorhandler(500)
def error_interno_servidor(error):
    """
    Maneja errores 500 (errores internos del servidor).
    """
    breadcrumbs = [
        {'name': 'Inicio', 'url': url_for('generales.index')},
        {'name': 'Error 500', 'url': '#'}
    ]
    logging.error(f"Error interno del servidor: {error}")
    return render_template('error.html', mensaje="Ha ocurrido un error inesperado. Por favor, intenta nuevamente más tarde.", breadcrumbs=breadcrumbs), 500