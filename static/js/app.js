// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    // Función genérica para mostrar confirmaciones
    function agregarConfirmacion(selector, mensajeCallback) {
        const buttons = document.querySelectorAll(selector);
        buttons.forEach((button) => {
            button.addEventListener('click', function (e) {
                const mensaje = mensajeCallback(button);
                const confirmacion = confirm(mensaje);
                if (!confirmacion) {
                    e.preventDefault(); // Cancelar la acción si el usuario no confirma
                }
            });
        });
    }

    // Confirmaciones específicas
    agregarConfirmacion('.btn-editar-rol', (button) => {
        const nombreUsuario = button.dataset.nombre;
        const rolActual = button.dataset.rol;
        return `¿Estás seguro de que deseas editar el rol del usuario "${nombreUsuario}" (Rol actual: ${rolActual})?`;
    });

    agregarConfirmacion('.btn-eliminar, .btn-confirmar, .btn-prestar', (button) => {
        const libroTitulo = button.dataset.titulo;
        const accion = button.classList.contains('btn-eliminar')
            ? 'eliminar'
            : button.classList.contains('btn-confirmar')
            ? 'devolver'
            : 'prestar';
        return `¿Estás seguro de que deseas ${accion} el libro "${libroTitulo}"?`;
    });

    // Validación de formularios
    function validarFormulario(form, validaciones) {
        form.addEventListener('submit', function (e) {
            let valido = true;
            validaciones.forEach((validacion) => {
                if (!validacion()) {
                    valido = false;
                    e.preventDefault(); // Evitar el envío del formulario
                }
            });
            return valido;
        });
    }

    // Validación del formulario de registro
    const registroForm = document.querySelector('#registro-form');
    if (registroForm) {
        validarFormulario(registroForm, [
            () => {
                const nombre = document.querySelector('#nombre').value.trim();
                const email = document.querySelector('#email').value.trim();
                const contrasena = document.querySelector('#contrasena').value.trim();
                if (!nombre || !email || !contrasena) {
                    alert('Por favor, completa todos los campos.');
                    return false;
                }
                return true;
            },
            () => {
                const email = document.querySelector('#email').value.trim();
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    alert('Por favor, ingresa un correo electrónico válido.');
                    return false;
                }
                return true;
            },
        ]);
    }

    // Validación del formulario de inicio de sesión
    const loginForm = document.querySelector('#login-form');
    if (loginForm) {
        validarFormulario(loginForm, [
            () => {
                const email = document.querySelector('#email').value.trim();
                const contrasena = document.querySelector('#contrasena').value.trim();
                if (!email || !contrasena) {
                    alert('Por favor, completa todos los campos.');
                    return false;
                }
                return true;
            },
        ]);
    }

    // Manejo de mensajes flash
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove(); // Eliminar el mensaje del DOM
            }, 500); // Eliminar el mensaje después de la animación
        }, 3000); // Mostrar el mensaje durante 3 segundos
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

    // Deshabilitar el botón de envío solo si el formulario pasa las validaciones
    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        form.addEventListener('submit', function (e) {
            // Verificar si el evento fue prevenido por alguna validación
            if (!e.defaultPrevented) {
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true; // Deshabilitar el botón para evitar múltiples envíos
                    submitButton.textContent = 'Procesando...'; // Cambiar el texto del botón
                }
            }
        });
    });
});