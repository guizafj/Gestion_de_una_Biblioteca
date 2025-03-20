from colorama import init, Fore, Back, Style

init(autoreset=True)  # Buenas prácticas: inicializar una vez al comienzo


class ConsoleFormatter:
    def __init__(self):
        self.fore = Fore
        self.back = Back
        self.style = Style

    def info(self, message):
        print(self.fore.CYAN + message)

    def warning(self, message):
        print(self.fore.YELLOW + message)

    def error(self, message):
        print(self.fore.RED + self.style.BRIGHT + message)

    def success(self, message):
        print(self.fore.GREEN + message)

    def custom(self, message, color=Fore.WHITE, bg=Back.BLACK, bold=False):
        style = self.style.BRIGHT if bold else self.style.NORMAL
        print(color + bg + style + message)


# Uso en otro lado del código
class App:
    def __init__(self):
        self.formatter = ConsoleFormatter()

    def run(self):
        self.formatter.info("Este es un mensaje informativo.")
        self.formatter.warning("Advertencia detectada.")
        self.formatter.error("Error fatal encontrado.")
        self.formatter.success("Operación exitosa.")
        self.formatter.custom("Mensaje personalizado", color=Fore.MAGENTA, bg=Back.WHITE, bold=True)


if __name__ == "__main__":
    app = App()
    app.run()
