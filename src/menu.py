from biblioteca import Biblioteca
from estilo import ConsoleFormatter

# Clase Menu: Representa el menú de interacción con el usuario.
class Menu:
    def __init__(self):
        self.biblioteca = Biblioteca()  # Se crea un objeto Biblioteca.
        self.estilo = ConsoleFormatter()

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
                self.estilo.success("Saliendo del programa...")
                break  # Salimos del bucle y terminamos el programa.

            else:  # Opción inválida.
                self.estilo.error("Opción inválida. Intenta de nuevo.")
