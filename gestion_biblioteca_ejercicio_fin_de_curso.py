from colorama import init, Fore, Back, Style 

# SISTEMA DE GESTIÓN DE BIBLIOTECA
# Este programa permite administrar una biblioteca mediante un menú interactivo, gestionado desde la consola.
# Se desarrollo implementando la Programación Orientada a Objetos (POO).

# Funcionalidades:
# - Agregar libros
# - Prestar libros
# - Devolver libros
# - Mostrar todos los libros
# - Buscar libros por ISBN
init(autoreset = True)  # Inicializa colorama y asegura que los estilos se reinicien automáticamente después de cada impresión

# Clase Libro: Representa un libro en la biblioteca.
class Libro:
    def __init__(self, s_titulo: str, s_autor: str, s_isbn: str): # El metodo __init__ es llamado al crear el objeto / Metodo constructor
        self.s_titulo = s_titulo.title()  # Atributo: Título del libro.
        self.s_autor = s_autor.title()    # Atributo: Autor del libro.
        self.s_isbn = s_isbn      # Atributo: ISBN del libro (identificador único).
        self.is_disponible = True  # Atributo: Estado de disponibilidad (True por defecto).

    # Método para prestar el libro.
    def prestar(self):
        if self.is_disponible:  # Si el libro está disponible...
            self.is_disponible = False  # Se marcara como no disponible.
            print(f"{Fore.GREEN}Libro '{self.s_titulo}' prestado con éxito.")
        else:  # Si el libro ya está prestado...
            print(f"{Fore.BLUE}El libro '{self.s_titulo}' ya está prestado.")

    # Método para devolver el libro.
    def devolver(self):
        if not self.is_disponible:  # Si el libro no está disponible...
            self.is_disponible = True  # Se marca como disponible.
            print(f"{Fore.YELLOW}Libro '{self.s_titulo}' devuelto con éxito.")
        else:  # Si el libro ya está disponible...
            print(f"{Fore.CYAN}El libro '{self.s_titulo}' ya estába disponible.")

    # Método para mostrar la información del libro.
    def mostrar(self):
        estado = "Sí" if self.is_disponible else "No"  # Convertimos el estado a "Sí" o "No".
        print(f"-{Fore.MAGENTA} {self.s_titulo} ({self.s_autor}) - ISBN: {self.s_isbn} - Disponible: {estado}")

    # Método para buscar un libro por su ISBN.
    def buscar(self, s_isbn):
        return self.s_isbn == s_isbn  # Devuelve True si el ISBN coincide.

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

# Clase Menu: Representa el menú de interacción con el usuario.
class Menu:
    def __init__(self):
        self.biblioteca = Biblioteca()  # Se crea un objeto Biblioteca.

    # Método para mostrar el menú y manejar las opciones del usuario.
    def mostrar_menu(self):
        while True:  # Bucle infinito para mantener el programa en ejecución.
            print("\nBienvenido al Sistema de Gestión de Biblioteca")
            print("1. Agregar libro")
            print("2. Prestar libro")
            print("3. Devolver libro")
            print("4. Mostrar libros")
            print("5. Buscar libro por ISBN")
            print("6. Salir")
            opcion = input("Elige una opción: ")  # Se pide al usuario la  opción deseada.

            if opcion == "1":  # Agregar un libro.
                titulo = input("Título: ")
                autor = input("Autor: ")
                isbn = input("ISBN: ")
                self.biblioteca.agregar_libro(titulo, autor, isbn)

            elif opcion == "2":  # Prestar un libro.
                isbn = input("Ingresa el ISBN: ")
                self.biblioteca.prestar_libro(isbn)

            elif opcion == "3":  # Devolver un libro.
                isbn = input("Ingresa el ISBN: ")
                self.biblioteca.devolver_libro(isbn)

            elif opcion == "4":  # Mostrar todos los libros.
                self.biblioteca.mostrar_libros()

            elif opcion == "5":  # Buscar un libro por ISBN.
                isbn = input("Ingresa el ISBN: ")
                self.biblioteca.buscar_libro(isbn)

            elif opcion == "6":  # Salir del programa.
                print("Saliendo del programa...")
                break  # Salimos del bucle y terminamos el programa.

            else:  # Opción inválida.
                print(f"{Fore.RED} Opción inválida. Intenta de nuevo.")

# Punto de entrada del programa.
if __name__ == "__main__":
    menu = Menu()  # Creamos un objeto Menu.
    menu.mostrar_menu()  # Llamamos al método para mostrar el menú.