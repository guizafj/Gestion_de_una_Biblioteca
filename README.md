# 📚 Sistema de Gestión y Administración de Biblioteca

Este proyecto es una aplicación que estoy empezando a construir para la **gestión y administración de una biblioteca**. Actualmente se encuentra en una fase inicial y está en pleno desarrollo.

## 🚀 Características previstas

## Funcionalidades

- **Gestión de Libros**:

  - Agregar, editar y eliminar libros.
  - Validar ISBN único (10 o 13 dígitos).
  - Validar títulos únicos.
  - Agrupar libros por autor.

- **Préstamos y Devoluciones**:

  - Prestar y devolver libros.
  - Historial de préstamos.
  - Recordatorios de devoluciones pendientes.

- **Autenticación de Usuarios**:

  - Registro de usuarios con confirmación de correo electrónico.
  - Inicio de sesión seguro.
  - Roles de usuario: "bibliotecario" y "usuario".

- **Búsqueda Avanzada**:

  - Buscar libros por título, autor o ISBN.

- **Escalabilidad**:

- Estructura modular para facilitar futuras mejoras.
- Gestión de inventario de libros (altas, bajas y modificaciones)
- Control de préstamos y devoluciones de libros
- Administración de usuarios (lectores, administradores)
- Historial de transacciones y reportes básicos

## 🛠️ Tecnologías planificadas

- **Python** (backend)
- **SQLite** o **PostgreSQL** (base de datos)
- **Flask** (para desarrollo y despliegue en servidores)
- **Visual Studio Code** (entorno de desarrollo)

## ✅ Estado actual del proyecto

  ⚠️ En construcción - Fase inicial

    Estoy comenzando la creación de la estructura base del proyecto y las primeras funcionalidades.
    ### ** Resumen de Mejoras Implementadas**

      1. **Confirmación de Correo Electrónico**:
        - Se implementó un sistema de confirmación de correo usando tokens únicos generados con `secrets`.
        - Los usuarios deben confirmar su correo antes de iniciar sesión.

      2. **Roles de Usuario**:
        - Se añadió un campo `rol` al modelo `Usuario` para diferenciar entre bibliotecarios y usuarios regulares.
        - Se implementaron restricciones de acceso basadas en roles.  

      3. **Gestión de Libros**:
         - Se añadieron rutas y plantillas para editar y eliminar libros.
        - Se validó el ISBN (10 o 13 dígitos) y se verificó que los títulos sean únicos.

      4. **Préstamos y Devoluciones**:
        - Se implementó un sistema de préstamos y devoluciones con historial.
        - Se añadieron recordatorios para devoluciones pendientes. 
      
      5. **Búsqueda Avanzada**:
        - Se permitió buscar libros por título, autor o ISBN.

      6. **Estructura Modular**:
        - El proyecto sigue una estructura modular clara, facilitando futuras mejoras. 

## 🎯 Objetivo general

  Aplicación web para gestionar una biblioteca utilizando Flask, SQLAlchemy y autenticación de usuarios. 
  Incluye funcionalidades como registro de usuarios, confirmación de correo electrónico, gestión de libros, préstamos, devoluciones y más.

  ## Mejoras Futuras 

    Implementar notificaciones automáticas para recordatorios de devolución.
    Añadir pruebas unitarias para mejorar la calidad del código.
    Se esta migrando actualmente a MySQL la base de datos
    Agregar la variable de cantidad en el modelo de libro
    Se cambiara la forma de prestar libros, el usuario registrado podra reservarlo, mas no crear un prestamos, ya que eso es una función del bibliotecario
     

## 🤝 Contribuciones

  Como el proyecto está en sus primeras etapas, cualquier sugerencia o feedback es bienvenido. En el futuro estaré abierto a colaboraciones externas.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/guizafj/Gestion_de_una_Biblioteca.git
   cd Gestion_y_Administracion_de_una_Biblioteca  

## 📦 Estructura del proyecto (en progreso)

```plaintext
biblioteca_flask/
├── app.py                  # Archivo principal de la aplicación
├── modules/                # Carpeta para módulos independientes
|   |__ __init__.py         # Este archivo marca el directorio como un paquete de Python.
│   ├── models.py           # Definición de modelos (libros, usuarios, préstamos)
│   ├── forms.py            # Formularios usando Flask-WTF
│   ├── routes.py           # Rutas y lógica de negocio
│   └── auth.py             # Lógica de autenticación
├── templates/              # Archivos HTML
|   ├── agregar_libro.html  # Formulario para agregar libros
|   ├── autores.html        # Pagina de autores contenidos en la biblioteca
│   ├── base.html           # Plantilla base
│   ├── buscar_libro.html   # Página de búsqueda
│   ├── devolver_libro.html # Formulario para devolver libros
|   ├── editar_libro.html    # Formulario para editar libros
|   ├── editar_rol.html     # Formulario para modificar el rol de usuarios en la biblioteca
|   ├── eliminar_libro.html # Formulario para eliminar libros
|   ├── error.html          # Pagina para mostrar errores en la aplicación
|   ├── gestion_libros.html # Pagina para gestionar los libros contenidos en la biblioteca
|   ├── historial.html      # Se muestra el historial de prestamos por el usuario
│   ├── index.html          # Página principal
│   ├── login.html          # Página de inicio de sesión
│   ├── prestar_libro.html  # Formulario para prestar libros
│   ├── registro.html       # Página de registro de usuarios
|   ├── recordatorios.html  # Visualizacion de recordatorios por usuario
│   └── historial.html      # Historial de préstamos
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
│   ├── css/
│   │   └── styles.css      # Hoja de estilos CSS
│   └── js/
│       └── scripts.js      # Archivo JavaScript
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación del proyecto