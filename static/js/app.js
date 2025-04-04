// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    // Validación del formulario de registro
    const registroForm = document.querySelector('#registro-form');
    if (registroForm) {
        registroForm.addEventListener('submit', function (e) {
            const nombre = document.querySelector('#nombre').value.trim();
            const email = document.querySelector('#email').value.trim();
            const contrasena = document.querySelector('#contrasena').value.trim();

            // Validar campos vacíos
            if (!nombre || !email || !contrasena) {
                e.preventDefault(); // Evitar el envío del formulario
                alert('Por favor, completa todos los campos.');
            }

            // Validar formato de correo electrónico
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                e.preventDefault(); // Evitar el envío del formulario
                alert('Por favor, ingresa un correo electrónico válido.');
            }
        });
    }

    // Validación del formulario de inicio de sesión
    const loginForm = document.querySelector('#login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            const email = document.querySelector('#email').value.trim();
            const contrasena = document.querySelector('#contrasena').value.trim();

            // Validar campos vacíos
            if (!email || !contrasena) {
                e.preventDefault(); // Evitar el envío del formulario
                alert('Por favor, completa todos los campos.');
            }
        });
    }

    // Manejo de mensajes flash
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 500); // Eliminar el mensaje después de la animación
        }, 3000); // Mostrar el mensaje durante 3 segundos
    });

    // Animación para botones de navegación
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach((link) => {
        link.addEventListener('click', function (e) {
            e.target.classList.add('clicked'); // Agregar una clase temporal
            setTimeout(() => {
                e.target.classList.remove('clicked');
            }, 200); // Remover la clase después de la animación
        });
    });

    // Mejora visual para campos de entrada
    const inputFields = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
    inputFields.forEach((input) => {
        input.addEventListener('focus', function () {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function () {
            if (!this.value.trim()) {
                this.parentElement.classList.remove('focused');
            }
        });
    });

    // Función para buscar libros
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function (e) {
            const query = document.querySelector('#search-query').value.trim();
            if (!query) {
                e.preventDefault(); // Evitar el envío del formulario
                alert('Por favor, ingresa un término de búsqueda.');
            }
        });
    }

    // Confirmación antes de eliminar libros
    const deleteButtons = document.querySelectorAll('.btn-eliminar');
    deleteButtons.forEach((button) => {
        button.addEventListener('click', function (e) {
            const libroTitulo = button.dataset.titulo; // Asegúrate de agregar `data-titulo` en los botones
            const confirmacion = confirm(`¿Estás seguro de que deseas eliminar el libro "${libroTitulo}"?`);
            if (!confirmacion) {
                e.preventDefault(); // Cancelar la acción si el usuario no confirma
            }
        });
    });

    // Efectos visuales para formularios
    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        form.addEventListener('submit', function () {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true; // Deshabilitar el botón para evitar múltiples envíos
                submitButton.textContent = 'Procesando...'; // Cambiar el texto del botón
            }
        });
    });
});