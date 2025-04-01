# 📚 Sistema de Gestión y Administración de Biblioteca

Este proyecto es una aplicación que estoy empezando a construir para la **gestión y administración de una biblioteca**. Actualmente se encuentra en una fase inicial y está en pleno desarrollo.

## 🚀 Características previstas

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

## 🎯 Objetivo general

  Desarrollar un sistema simple, modular y eficiente que facilite la administración de bibliotecas pequeñas o medianas, aplicando buenas prácticas de programación.
  Diseñar un sistema extensible y adaptable a diferentes tipos de bibliotecas.

## 🤝 Contribuciones

  Como el proyecto está en sus primeras etapas, cualquier sugerencia o feedback es bienvenido. En el futuro estaré abierto a colaboraciones externas.

## 📦 Estructura del proyecto (en progreso)

```plaintext
biblioteca_flask/
├── app.py                  # Archivo principal de la aplicación
├── modules/                # Carpeta para módulos independientes
│   ├── models.py           # Definición de modelos (libros, usuarios)
│   ├── forms.py            # Formularios usando Flask-WTF
│   ├── routes.py           # Rutas y lógica de negocio
│   └── auth.py             # Lógica de autenticación
├── templates/              # Archivos HTML
│   ├── base.html           # Plantilla base
│   ├── index.html          # Página principal
│   ├── agregar_libro.html  # Formulario para agregar libros
│   ├── buscar_libro.html   # Página de búsqueda
│   ├── login.html          # Página de inicio de sesión
│   └── registro.html       # Página de registro de usuarios
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
│   ├── css/
│   │   └── styles.css      # Hoja de estilos CSS
│   └── js/
│       └── scripts.js      # Archivo JavaScript
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación del proyecto
