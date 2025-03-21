from estilo import ConsoleFormatter

# Clase Libro: Representa un libro en la biblioteca.
class Libro:
    def __init__(self, s_titulo: str, s_autor: str, s_isbn: str): # El metodo __init__ es llamado al crear el objeto / Metodo constructor
        self.s_titulo = s_titulo.title()  # Atributo: Título del libro.
        self.s_autor = s_autor.title()    # Atributo: Autor del libro.
        self.s_isbn = s_isbn      # Atributo: ISBN del libro (identificador único).
        self.is_disponible = True  # Atributo: Estado de disponibilidad (True por defecto).
        self.estilo = ConsoleFormatter()  # Se crea un nuevo objeto console formatter

    # Método para prestar el libro.
    def prestar(self):
        if self.is_disponible:  # Si el libro está disponible...
            self.is_disponible = False  # Se marcara como no disponible.
            self.estilo.success(f"Libro '{self.s_titulo}' prestado con éxito.")
        else:  # Si el libro ya está prestado...
            self.estilo.info(f"El libro '{self.s_titulo}' ya está prestado.")

    # Método para devolver el libro.
    def devolver(self):
        if not self.is_disponible:  # Si el libro no está disponible...
            self.is_disponible = True  # Se marca como disponible.
            self.estilo.success(f"Libro '{self.s_titulo}' devuelto con éxito.")
        else:  # Si el libro ya está disponible...
            self.estilo.info(f"El libro '{self.s_titulo}' ya estába disponible.")

    # Método para mostrar la información del libro.
    def mostrar(self):
        estado = "Sí" if self.is_disponible else "No"  # Convertimos el estado a "Sí" o "No".
        self.estilo.presentacion(f"-{self.s_titulo} ({self.s_autor}) - ISBN: {self.s_isbn} - Disponible: {estado}")

    # Método para buscar un libro por su ISBN.
    def buscar(self, s_isbn):
        return self.s_isbn == s_isbn  # Devuelve True si el ISBN coincide.
