# Sistema de Gestión y Administración de Biblioteca

Aplicación web para la gestión y administración de bibliotecas, desarrollada con Flask y MySQL/MariaDB. Proyecto en desarrollo activo, orientado a ser donado a instituciones públicas.

## Características

### Gestión de Libros
- CRUD completo (agregar, editar, eliminar)
- Validación de ISBN-10/ISBN-13 con checksum
- Búsqueda por título, autor, ISBN, género o editorial
- Importación de libros desde CSV
- Agrupación por autor, género y título
- Control de cantidad de ejemplares

### Préstamos y Devoluciones
- Sistema de préstamos con control de cantidad
- Reserva de libros por usuarios (pendiente/aprobada/rechazada)
- Aprobación/rechazo de reservas por bibliotecario
- Expiración automática de reservas (7 días)
- Historial personal y general de préstamos
- Recordatorios de devoluciones pendientes
- Libros más prestados

### Autenticación y Seguridad
- Registro con confirmación de correo electrónico
- Login/logout con Flask-Login
- Roles: usuario, bibliotecario, administrador
- Control de acceso basado en roles
- Bloqueo de cuenta tras 5 intentos fallidos
- Recuperación de contraseña vía email

### Infraestructura
- Docker Compose (app + MariaDB 10.11)
- Migraciones con Flask-Migrate (Alembic)
- Tests unitarios, de rutas e integración (150 tests)
- Pre-commit hooks (ruff lint + format)

## Tecnologías

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11, Flask 3.1.3 |
| ORM | SQLAlchemy + Flask-Migrate |
| Base de datos | MySQL/MariaDB 10.11 (producción), SQLite (tests) |
| Autenticación | Flask-Login |
| Email | Flask-Mail |
| Formularios | Flask-WTF |
| Paquete | Gunicorn (producción), PDM (desarrollo) |
| Contenedores | Docker, Docker Compose |

## Instalación

### Desarrollo local

```bash
# Clonar el repositorio
git clone https://github.com/guizafj/Gestion_de_una_Biblioteca.git
cd Gestion_de_una_Biblioteca

# Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pdm install

# Configurar variables de entorno (editar .env con tus credenciales)
cp .env.example .env

# Inicializar la base de datos
python iniciar_base_de_datos.py

# Crear usuario administrador
python crear_admin.py

# Ejecutar la aplicación
python main.py  # http://localhost:5000
```

### Docker

```bash
# Construir y ejecutar
docker-compose up --build

# La app estará en http://localhost:5000
# MariaDB estará en localhost:3308
```

### Tests

```bash
python -m unittest discover tests  # 150 tests
```

## Estructura del proyecto

```
Gestion_de_una_Biblioteca/
├── main.py                     # App factory, blueprints, filtros
├── config.py                   # Configuración (MySQL, mail, cookies)
├── extensions.py               # Instancias db y mail
├── docker-compose.yml          # Orquestación Docker
├── Dockerfile                  # Imagen de la app
├── pyproject.toml              # Dependencias (PDM)
├── .env                        # Variables de entorno (no committear)
├── src/
│   ├── models/                 # Modelos SQLAlchemy
│   │   ├── models_libro.py     # Libro (CRUD, validaciones)
│   │   ├── models_usuario.py   # Usuario (auth, roles, tokens)
│   │   ├── models_prestamo.py  # Préstamo (ciclo de vida)
│   │   └── models_reserva.py   # Reserva (flujo de aprobación)
│   ├── routes/                 # Blueprints
│   │   ├── routes_generales.py # Index, favicon, errores
│   │   ├── routes_auth.py      # Login, registro, recuperación
│   │   ├── routes_usuarios.py  # Gestión de usuarios (admin)
│   │   ├── routes_libros.py    # CRUD libros, búsqueda, importación
│   │   └── routes_prestamos.py # Préstamos, reservas, historial
│   ├── forms/forms.py          # WTForms
│   ├── auth.py                 # Flask-Login load_user
│   └── permissions.py          # Decoradores de roles
├── templates/                  # Jinja2 (29 templates + 3 emails)
├── static/                     # CSS, JS, favicon
├── migrations/                 # Alembic (3 migraciones)
├── tests/                      # 150 tests
│   ├── test_models.py          # 79 tests unitarios
│   ├── test_routes.py          # 52 tests de rutas
│   ├── test_flujo.py           # 12 tests de integración
│   └── test_app.py             # 7 tests de smoke
└── .docs/                      # Documentación interna
```

## Roles y permisos

| Rol | Permisos |
|---|---|
| `usuario` | Buscar libros, reservar, ver historial personal |
| `bibliotecario` | + Prestar/devolver, gestionar libros, ver recordatorios |
| `admin` | + Gestionar usuarios, importar CSV, historial general |

## Estado actual

### Implementado
- CRUD de libros con validaciones
- Sistema de usuarios con roles y autenticación
- Préstamos y devoluciones con control de inventario
- Reservas con flujo de aprobación
- Búsqueda avanzada e importación CSV
- 150 tests (unitarios, rutas, integración)
- Docker Compose con MariaDB
- Migraciones de base de datos

### Pendiente
- Notificaciones automáticas de devolución
- Marcar préstamos vencidos (cron job)
- Sistema de penalizaciones (modelo existe, sin UI)
- Rate limiting (`flask-limiter` instalado, sin inicializar)
- CSRF protection (`flask-seasurf` instalado, sin inicializar)
- Debug toolbar (instalado, sin usar)
- Template `notificacion_general.html` (referenciado, no existe)

## Licencia

MIT

## Autor

Francisco Javier - [contacto@dguiza.dev](mailto:contacto@dguiza.dev)
