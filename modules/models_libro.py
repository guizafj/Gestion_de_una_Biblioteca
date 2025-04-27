from extensions import db
import re
import logging


class Libro(db.Model):
    """
    Representa un libro en la biblioteca.
        Atributos:
            id (int): Identificador único del libro (clave primaria).
            isbn (str): Número de Identificación Estándar de Libro (ISBN), debe ser único.
            titulo (str): Título del libro.
            autor (str): Nombre del autor del libro.
            cantidad (int): Número total de copias del libro disponibles.
            disponible (bool): Indica si hay al menos una copia del libro disponible para préstamo.
    """
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True) # Índice para ISBN
    titulo = db.Column(db.String(100), nullable=False, index=True) # Índice para título
    autor = db.Column(db.String(100), nullable=False, index=True) # Índice para autor
    cantidad = db.Column(db.Integer, nullable=False)
    # disponible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Libro {self.titulo}>"
    
    @property
    def esta_disponible(self):
        return self.cantidad > 0

    @staticmethod
    def _limpiar_isbn(isbn):
        """Elimina guiones y espacios del ISBN."""
        return isbn.replace("-", "").replace(" ", "")

    @staticmethod
    def _es_isbn10_valido(isbn):
        """Verifica si un ISBN-10 es válido."""
        if len(isbn) != 10 or not isbn[:-1].isdigit() or (isbn[-1] not in "0123456789X"):
            return False

        suma = sum((10 - i) * (10 if digito == 'X' else int(digito)) for i, digito in enumerate(isbn))
        return suma % 11 == 0

    @staticmethod
    def _es_isbn13_valido(isbn):
        """Verifica si un ISBN-13 es válido."""
        if len(isbn) != 13 or not isbn.isdigit():
            return False

        suma = sum((3 if i % 2 else 1) * int(digito) for i, digito in enumerate(isbn[:-1]))
        digito_verificacion = (10 - (suma % 10)) % 10
        return digito_verificacion == int(isbn[-1])

    @staticmethod
    def validar_isbn(isbn, libro_id=None):
        """
        Valida que el ISBN sea válido (ISBN-10 o ISBN-13) y único en la base de datos.
        """
        if not isbn or isbn.strip() == "":
            raise ValueError("El ISBN no puede estar vacío.")

        isbn_limpio = Libro._limpiar_isbn(isbn)

        if not isbn_limpio.isdigit() and not (isbn_limpio[:-1].isdigit() and isbn_limpio[-1] in "0123456789X"):
            raise ValueError("El ISBN contiene caracteres no válidos.")

        es_valido = False
        if len(isbn_limpio) == 10:
            es_valido = Libro._es_isbn10_valido(isbn_limpio)
        elif len(isbn_limpio) == 13:
            es_valido = Libro._es_isbn13_valido(isbn_limpio)

        if not es_valido:
            raise ValueError("El ISBN no es válido. Ejemplo de ISBN-10: '0-306-40615-2'. Ejemplo de ISBN-13: '978-3-16-148410-0'.")

        libro = Libro.query.filter_by(isbn=isbn).first()
        if libro and (libro_id is None or libro.id != libro_id):
            raise ValueError("El ISBN ya existe en la base de datos.")

        return isbn_limpio
    
    @staticmethod
    def validar_titulo(titulo, libro_id=None):
        """
        Valida que el título no esté duplicado en la base de datos.
        Args:
            titulo (str): El título a validar.
            libro_id (int): El ID del libro actual (opcional, para excluirlo de la validación).
        Returns:
            str: El título validado.
        Raises:
            ValueError: Si el título ya existe en la base de datos.
        """
        # Verificar que el título no esté vacío
        if not titulo or titulo.strip() == "":
            raise ValueError("El título no puede estar vacío.")
        
        # Validar formato del titulo (solo letras, espacios y caracteres especiales básicos)
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-]+$", titulo):
            raise ValueError("El autor solo puede contener letras, espacios, puntos y guiones.")

    
        # Validar unicidad del título
        libro = Libro.query.filter_by(titulo=titulo).first()
        if libro and (libro_id is None or libro.id != libro_id):
            raise ValueError("El título ya existe en la base de datos.")
        return titulo
    
    @staticmethod
    def validar_autor(autor):
        """
        Valida que el autor no esté vacío y tenga un formato adecuado.
        Args:
            autor (str): El autor a validar.
        Returns:
            str: El autor validado.
        Raises:
            ValueError: Si el autor no es válido.
        """
        # Verificar que el autor no esté vacío
        if not autor or autor.strip() == "":
            raise ValueError("El autor no puede estar vacío.")
        
        # Validar formato del autor (solo letras, espacios y caracteres especiales básicos)
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-]+$", autor):
            raise ValueError("El autor solo puede contener letras, espacios, puntos y guiones.")

        return autor
  
    @staticmethod
    def validar_cantidad(cantidad):
        """
        Valida que la cantidad sea un número entero positivo.
        Args:
            cantidad (int): La cantidad a validar.
        Returns:
            int: La cantidad validada.
        Raises:
            ValueError: Si la cantidad no es válida.
        """
        # Verificar que la cantidad no esté vacía
        if cantidad is None or str(cantidad).strip() == "":
            raise ValueError("La cantidad no puede estar vacía.")

        # Verificar que la cantidad sea un número entero
        if not str(cantidad).isdigit():
            raise ValueError("La cantidad debe ser un número entero.")

        # Verificar que la cantidad sea mayor que 0
        cantidad = int(cantidad)
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")

        return cantidad

    @classmethod
    def contar_libros(cls):
        """
        Cuenta el número total de libros en la biblioteca.
        """
        return cls.query.count()

    def esta_disponible(self):
        """
        Verifica si hay ejemplares disponibles para préstamo.
        """
        return self.cantidad > 0

    def reducir_cantidad(self):
        """
        Reduce la cantidad disponible en 1 al realizar un préstamo.
        """
        if self.cantidad <= 0:
            raise ValueError("No hay ejemplares disponibles para préstamo.")
        self.cantidad -= 1

    def incrementar_cantidad(self):
        """
        Incrementa la cantidad disponible en 1 al devolver un préstamo.
        """
        self.cantidad += 1
