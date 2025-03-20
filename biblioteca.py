from libro import Libro
from colorama import init, Fore, Back, Style 
init(autoreset = True)  # Inicializa colorama y asegura que los estilos se reinicien automáticamente después de cada impresión
# Clase Biblioteca: Representa la biblioteca y gestiona los libros.
class Biblioteca:
    def __init__(self):
        self.libros = []  # Atributo: Lista de libros en la biblioteca.

    # Método para agregar un nuevo libro a la biblioteca.
    def agregar_libro(self, s_titulo, s_autor, s_isbn):
        libro = Libro(s_titulo, s_autor, s_isbn)  # Se crea un nuevo objeto Libro.
        self.libros.append(libro)  # Se añade a la lista de libros.
        print(f"{Fore.GREEN}Libro '{s_titulo}' agregado con éxito.")

    # Método para prestar un libro por su ISBN.
    def prestar_libro(self, s_isbn):
        for libro in self.libros:  # Haciendo uso del for se recorre la lista de libros.
            if libro.buscar(s_isbn):  # Si encontramos el libro por su ISBN...
                libro.prestar()  # Se llama al metodo prestar y Lo prestamos.
                return  # Salimos del método después de prestar el libro.
        print(f"{Fore.RED} Libro no encontrado.")  # Si no encontramos el libro, mostramos un mensaje.

    # Método para devolver un libro por su ISBN.
    def devolver_libro(self, s_isbn):
        for libro in self.libros:  # Se Recorre la lista de libros.
            if libro.buscar(s_isbn):  # Si se encuentra el libro por su ISBN...
                libro.devolver()  # Lo devolvemos.
                return  # Salimos del método después de devolver el libro.
        print(f"{Fore.YELLOW} Libro no encontrado.")  # Si no encontramos el libro, mostramos un mensaje.

    # Método para mostrar todos los libros en la biblioteca.
    def mostrar_libros(self):
        if not self.libros:  # Si no hay libros en la biblioteca...
            print(f"{Fore.CYAN} No hay libros en la biblioteca.")
        else:  # Si hay libros...
            for libro in self.libros:  # Recorremos la lista de libros.
                libro.mostrar()  # Mostramos la información de cada libro, llamando al metodo declarado en la clase Libro

    # Método para buscar un libro por su ISBN y mostrar su información.
    def buscar_libro(self, s_isbn):
        for libro in self.libros:  # Se recorre la lista de libros.
            if libro.buscar(s_isbn):  # Si se encuentra el libro por su ISBN...
                libro.mostrar()  # Mostramos su información.
                return  # Salimos del método después de mostrar el libro.
        print(f"{Fore.LIGHTBLUE_EX} Libro no encontrado.")  # Si no encontramos el libro, mostramos un mensaje.

