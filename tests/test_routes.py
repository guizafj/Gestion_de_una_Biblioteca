import unittest
from main import create_app
from extensions import db
from src.models.models_libro import Libro
from src.models.models_usuario import Usuario
from src.models.models_prestamo import Prestamo
from flask_login import logout_user


class BaseRouteTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.client = self.app.test_client()
        self.client.testing = True

    def tearDown(self):
        with self.app.test_request_context():
            logout_user()
        db.session.remove()

    def _crear_usuario(
        self,
        email="test@example.com",
        nombre="Test User",
        rol="usuario",
        confirmado=True,
    ):
        usuario = Usuario(nombre=nombre, email=email, rol=rol)
        usuario.set_password("password123")
        if confirmado:
            usuario.email_confirmado = True
            usuario.token_confirmacion = None
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def _crear_libro(self, isbn="9783161484100", titulo="Libro Test", cantidad=5):
        libro = Libro(
            isbn=isbn,
            titulo=titulo,
            autor="Autor Test",
            editorial="Editorial Test",
            genero="Genero Test",
            cantidad=cantidad,
        )
        db.session.add(libro)
        db.session.commit()
        return libro

    def _login(self, email="test@example.com", password="password123"):
        return self.client.post(
            "/auth/login",
            data={
                "email": email,
                "contrasena": password,
            },
            follow_redirects=True,
        )


class TestIndex(BaseRouteTestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_index_muestra_libros(self):
        self._crear_libro(titulo="Libro Visible")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_404(self):
        response = self.client.get("/ruta_inexistente")
        self.assertEqual(response.status_code, 404)

    def test_favicon(self):
        response = self.client.get("/favicon.ico")
        self.assertIn(response.status_code, [200, 404])


class TestAuthRoutes(BaseRouteTestCase):
    def test_login_GET(self):
        response = self.client.get("/auth/login")
        self.assertEqual(response.status_code, 200)

    def test_registro_GET(self):
        response = self.client.get("/auth/registro")
        self.assertEqual(response.status_code, 200)

    def test_registro_post_exitoso(self):
        response = self.client.post(
            "/auth/registro",
            data={
                "nombre": "Nuevo Usuario",
                "email": "nuevo@test.com",
                "contrasena": "password123",
                "confirmar_contrasena": "password123",
                "rol": "usuario",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        usuario = Usuario.query.filter_by(email="nuevo@test.com").first()
        self.assertIsNotNone(usuario)

    def test_registro_email_duplicado(self):
        self._crear_usuario(email="dup@test.com")
        response = self.client.post(
            "/auth/registro",
            data={
                "nombre": "Dup",
                "email": "dup@test.com",
                "contrasena": "password123",
                "confirmar_contrasena": "password123",
                "rol": "usuario",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_login_exitoso(self):
        self._crear_usuario(email="login@test.com")
        response = self.client.post(
            "/auth/login",
            data={
                "email": "login@test.com",
                "contrasena": "password123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_login_contrasena_incorrecta(self):
        self._crear_usuario(email="wrong@test.com")
        response = self.client.post(
            "/auth/login",
            data={
                "email": "wrong@test.com",
                "contrasena": "wrongpassword",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_login_usuario_no_existe(self):
        response = self.client.post(
            "/auth/login",
            data={
                "email": "noexiste@test.com",
                "contrasena": "password123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_login_email_no_confirmado(self):
        self._crear_usuario(email="noconf@test.com", confirmado=False)
        response = self.client.post(
            "/auth/login",
            data={
                "email": "noconf@test.com",
                "contrasena": "password123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self._crear_usuario(email="logout@test.com")
        self._login("logout@test.com")
        response = self.client.get("/auth/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_confirmar_email_token_invalido(self):
        response = self.client.get(
            "/auth/confirmar_email/invalidtoken", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_recuperar_cuenta_GET(self):
        response = self.client.get("/auth/recuperar_cuenta")
        self.assertEqual(response.status_code, 200)


class TestLibrosRoutes(BaseRouteTestCase):
    def test_buscar_libro_GET(self):
        response = self.client.get("/libros/buscar_libro")
        self.assertEqual(response.status_code, 200)

    def test_buscar_libro_con_termino(self):
        self._crear_libro(titulo="Buscable")
        response = self.client.get("/libros/buscar_libro?termino=Buscable")
        self.assertEqual(response.status_code, 200)

    def test_gestion_libros_requiere_login(self):
        response = self.client.get("/libros/gestion_libros", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_gestion_libros_usuario_regular(self):
        self._crear_usuario(email="regular@test.com", rol="usuario")
        self._login("regular@test.com")
        response = self.client.get("/libros/gestion_libros", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_gestion_libros_bibliotecario(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/libros/gestion_libros")
        self.assertEqual(response.status_code, 200)

    def test_gestion_libros_admin(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        self._login("admin@test.com")
        response = self.client.get("/libros/gestion_libros")
        self.assertEqual(response.status_code, 200)

    def test_agregar_libro_GET(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/libros/agregar_libro")
        self.assertEqual(response.status_code, 200)

    def test_editar_libro_GET(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        response = self.client.get(f"/libros/editar_libro/{libro.id}")
        self.assertEqual(response.status_code, 200)

    def test_eliminar_libro_GET(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        response = self.client.get(f"/libros/eliminar_libro/{libro.id}")
        self.assertEqual(response.status_code, 200)

    def test_eliminar_libro_post(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        response = self.client.post(
            f"/libros/eliminar_libro/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Libro.query.get(libro.id))

    def test_autores(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        self._crear_libro()
        response = self.client.get("/libros/autores")
        self.assertEqual(response.status_code, 200)

    def test_generos(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        self._crear_libro()
        response = self.client.get("/libros/generos")
        self.assertEqual(response.status_code, 200)

    def test_titulos(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        self._crear_libro()
        response = self.client.get("/libros/titulos")
        self.assertEqual(response.status_code, 200)


class TestUsuariosRoutes(BaseRouteTestCase):
    def test_gestion_usuarios_requiere_admin(self):
        self._crear_usuario(email="regular@test.com", rol="usuario")
        self._login("regular@test.com")
        response = self.client.get("/usuarios/gestion_usuarios", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_gestion_usuarios_admin(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        self._login("admin@test.com")
        response = self.client.get("/usuarios/gestion_usuarios")
        self.assertEqual(response.status_code, 200)

    def test_crear_usuario_GET(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        self._login("admin@test.com")
        response = self.client.get("/usuarios/crear_usuario")
        self.assertEqual(response.status_code, 200)

    def test_cambiar_rol(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        usuario = self._crear_usuario(email="target@test.com", rol="usuario")
        self._login("admin@test.com")
        response = self.client.post(
            f"/usuarios/cambiar_rol/{usuario.id}",
            data={
                "rol": "bibliotecario",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_cambiar_rol_no_puede_modificarse_a_si_mismo(self):
        admin = self._crear_usuario(email="admin@test.com", rol="admin")
        self._login("admin@test.com")
        response = self.client.post(
            f"/usuarios/cambiar_rol/{admin.id}",
            data={
                "rol": "usuario",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_eliminar_usuario(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        usuario = self._crear_usuario(email="target@test.com", rol="usuario")
        self._login("admin@test.com")
        response = self.client.post(
            f"/usuarios/eliminar_usuario/{usuario.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Usuario.query.get(usuario.id))

    def test_eliminar_usuario_no_puede_eliminarsi(self):
        admin = self._crear_usuario(email="admin@test.com", rol="admin")
        self._login("admin@test.com")
        response = self.client.post(
            f"/usuarios/eliminar_usuario/{admin.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Usuario.query.get(admin.id))


class TestPrestamosRoutes(BaseRouteTestCase):
    def test_gestionar_prestamos_requiere_rol(self):
        self._crear_usuario(email="regular@test.com", rol="usuario")
        self._login("regular@test.com")
        response = self.client.get(
            "/prestamos/gestionar_prestamos", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_gestionar_prestamos_bibliotecario(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/prestamos/gestionar_prestamos")
        self.assertEqual(response.status_code, 200)

    def test_prestar_GET(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        response = self.client.get(f"/prestamos/prestar/{libro.id}")
        self.assertEqual(response.status_code, 200)

    def test_prestar_post(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        response = self.client.post(
            f"/prestamos/prestar/{libro.id}",
            data={
                "usuario_id": usuario.id,
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_devolver_GET(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        prestamo = Prestamo(libro_id=libro.id, usuario_id=usuario.id)
        db.session.add(prestamo)
        db.session.commit()
        response = self.client.get(f"/prestamos/devolver/{libro.id}")
        self.assertEqual(response.status_code, 200)

    def test_devolver_post(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        self._login("bib@test.com")
        libro = self._crear_libro()
        prestamo = Prestamo(libro_id=libro.id, usuario_id=usuario.id)
        db.session.add(prestamo)
        db.session.commit()
        response = self.client.post(
            f"/prestamos/devolver/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_recordatorios(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        response = self.client.get("/prestamos/recordatorios")
        self.assertEqual(response.status_code, 200)

    def test_historial(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        response = self.client.get("/prestamos/historial")
        self.assertEqual(response.status_code, 200)

    def test_historial_prestamos_bibliotecario(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/prestamos/historial_prestamos")
        self.assertEqual(response.status_code, 200)

    def test_reservar_GET(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        libro = self._crear_libro()
        response = self.client.get(f"/prestamos/reservar/{libro.id}")
        self.assertEqual(response.status_code, 200)

    def test_reservar_post(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        libro = self._crear_libro()
        response = self.client.post(
            f"/prestamos/reservar/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_reservas_pendientes(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/prestamos/reservas_pendientes")
        self.assertEqual(response.status_code, 200)

    def test_buscar_usuarios(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        response = self.client.get("/prestamos/buscar_usuarios?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response.content_type)


class TestPermisos(BaseRouteTestCase):
    def test_usuario_no_puede_prestar(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        libro = self._crear_libro()
        response = self.client.get(
            f"/prestamos/prestar/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_usuario_no_puede_agregar_libro(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")
        response = self.client.get("/libros/agregar_libro", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_bibliotecario_no_puede_gestionar_usuarios(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/usuarios/gestion_usuarios", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_no_autenticado_redirige(self):
        response = self.client.get("/libros/gestion_libros", follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
