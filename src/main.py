# Implementaciones pendientes para mejorar el programa
"""
    - añadir validación para asegurar  que el ISBN es único al agregar un libro y asegurar que se ingresen correctamente. 
    - Implementar un método para guardar y cargar la lista de libros en un archivo para persistencia de datos. 
    - Considerar la opción de permitir editar la información de un libro ya existente. 
    - incluir un conteo de cuántos libros hay en total en la biblioteca y mostrarlos al final de la lista
    - agregar un método para eliminar un libro de la biblioteca si se desea. 
    - Utilizar un sistema de logging
    - permitir que el usuario no solo busque libros por ISBN, sino también por otros atributos como el título o el autor.
    - Añadir una confirmación antes de prestar o devolver un libro para evitar errores.
    - Implementar la funcionalidad de persistencia de datos para que los libros no se pierdan al cerrar el programa.
"""

from menu import Menu
# Punto de entrada del programa.
if __name__ == "__main__":
    menu = Menu()  # Creamos un objeto Menu.
    menu.mostrar_menu()  # Llamamos al método para mostrar el menú.