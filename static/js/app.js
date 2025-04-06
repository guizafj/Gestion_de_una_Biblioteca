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

    // Funciones de validación
    function campoNoVacio(valor) {
        return valor.trim() !== '';
    }

    function emailValido(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Función para validar un formulario
    function validarFormulario(form, validaciones) {
        form.addEventListener('submit', function (e) {
            let valido = true;
            validaciones.forEach((validacion) => {
                const campo = validacion.campo;
                const valor = campo.value.trim();
                const errorElement = document.getElementById(`${campo.id}-error`);

                if (!validacion.funcion(valor)) {
                    valido = false;
                    e.preventDefault();
                    if (errorElement) {
                        errorElement.style.display = 'block';
                    }
                } else {
                    if (errorElement) {
                        errorElement.style.display = 'none';
                    }
                }
            });
            return valido;
        });
    }

    // Validación del formulario de registro
    const registroForm = document.querySelector('#registro-form');
    if (registroForm) {
        validarFormulario(registroForm, [
            { campo: document.querySelector('#nombre'), funcion: campoNoVacio },
            { campo: document.querySelector('#email'), funcion: emailValido },
            { campo: document.querySelector('#contrasena'), funcion: campoNoVacio },
        ]);
    }

    // Validación del formulario de inicio de sesión
    const loginForm = document.querySelector('#login-form');
    if (loginForm) {
        validarFormulario(loginForm, [
            { campo: document.querySelector('#email'), funcion: campoNoVacio },
            { campo: document.querySelector('#contrasena'), funcion: campoNoVacio },
        ]);
    }

    // Manejo de mensajes flash
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach((message) => {
        setTimeout(() => {
            message.classList.add('fade');
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 3000);
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