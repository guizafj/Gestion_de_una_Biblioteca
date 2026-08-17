import unittest
from main import create_app
from extensions import db
from src.models.models_libro import Libro
from src.models.models_usuario import Usuario
from src.models.models_prestamo import Prestamo
from src.models.models_reserva import Reserva
from flask_login import logout_user


class TestFlujoCompleto(unittest.TestCase):
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

    def test_flujo_registro_login(self):
        response = self.client.post(
            "/auth/registro",
            data={
                "nombre": "Usuario Nuevo",
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
        self.assertFalse(usuario.email_confirmado)

        usuario.email_confirmado = True
        usuario.token_confirmacion = None
        db.session.commit()

        response = self._login("nuevo@test.com")
        self.assertEqual(response.status_code, 200)

    def test_flujo_prestamo_devolucion(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        libro = self._crear_libro(cantidad=3)

        self._login("bib@test.com")

        response = self.client.post(
            f"/prestamos/prestar/{libro.id}",
            data={
                "usuario_id": usuario.id,
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        prestamo = Prestamo.query.filter_by(
            libro_id=libro.id, usuario_id=usuario.id
        ).first()
        self.assertIsNotNone(prestamo)
        self.assertEqual(prestamo.estado, "activo")
        self.assertEqual(libro.cantidad, 2)

        response = self.client.post(
            f"/prestamos/devolver/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        prestamo_devuelto = Prestamo.query.get(prestamo.id)
        self.assertEqual(prestamo_devuelto.estado, "devuelto")
        self.assertIsNotNone(prestamo_devuelto.fecha_devolucion)
        self.assertEqual(libro.cantidad, 3)

    def test_flujo_reserva_aprobar_prestamo(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        libro = self._crear_libro(cantidad=1)

        self._login("lector@test.com")
        response = self.client.post(
            f"/prestamos/reservar/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        reserva = Reserva.query.filter_by(
            libro_id=libro.id, usuario_id=usuario.id
        ).first()
        self.assertIsNotNone(reserva)
        self.assertEqual(reserva.estado, "pendiente")

        self._login("bib@test.com")
        response = self.client.post(
            f"/prestamos/aprobar_reserva/{reserva.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        reserva_aprobada = Reserva.query.get(reserva.id)
        self.assertEqual(reserva_aprobada.estado, "aprobada")

        prestamo = Prestamo.query.filter_by(
            libro_id=libro.id, usuario_id=usuario.id
        ).first()
        self.assertIsNotNone(prestamo)
        self.assertEqual(prestamo.estado, "activo")

    def test_flujo_reserva_rechazar(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        libro = self._crear_libro()

        self._login("lector@test.com")
        self.client.post(f"/prestamos/reservar/{libro.id}", follow_redirects=True)

        reserva = Reserva.query.filter_by(
            libro_id=libro.id, usuario_id=usuario.id
        ).first()

        self._login("bib@test.com")
        response = self.client.post(
            f"/prestamos/rechazar_reserva/{reserva.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        reserva_rechazada = Reserva.query.get(reserva.id)
        self.assertEqual(reserva_rechazada.estado, "rechazada")

    def test_flujo_reserva_duplicada(self):
        self._crear_usuario(email="lector@test.com", rol="usuario")
        libro = self._crear_libro()

        self._login("lector@test.com")
        self.client.post(f"/prestamos/reservar/{libro.id}", follow_redirects=True)

        response = self.client.post(
            f"/prestamos/reservar/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_flujo_gestionar_usuario(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        usuario = self._crear_usuario(email="target@test.com", rol="usuario")

        self._login("admin@test.com")

        response = self.client.get("/usuarios/gestion_usuarios")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            f"/usuarios/cambiar_rol/{usuario.id}",
            data={
                "rol": "bibliotecario",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        usuario_actualizado = Usuario.query.get(usuario.id)
        self.assertEqual(usuario_actualizado.rol, "bibliotecario")

        response = self.client.post(
            f"/usuarios/eliminar_usuario/{usuario.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Usuario.query.get(usuario.id))

    def test_flujo_agregar_editar_eliminar_libro(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")

        response = self.client.post(
            "/libros/agregar_libro",
            data={
                "isbn": "9783161484100",
                "titulo": "Libro Nuevo",
                "autor": "Autor Nuevo",
                "editorial": "Editorial Nuevo",
                "genero": "Genero Nuevo",
                "cantidad": "5",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        libro = Libro.query.filter_by(isbn="9783161484100").first()
        self.assertIsNotNone(libro)
        self.assertEqual(libro.titulo, "Libro Nuevo")

        response = self.client.post(
            f"/libros/editar_libro/{libro.id}",
            data={
                "isbn": "9783161484100",
                "titulo": "Libro Editado",
                "autor": "Autor Editado",
                "editorial": "Editorial Editado",
                "genero": "Genero Editado",
                "cantidad": "10",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        libro_editado = Libro.query.get(libro.id)
        self.assertEqual(libro_editado.titulo, "Libro Editado")
        self.assertEqual(libro_editado.cantidad, 10)

        response = self.client.post(
            f"/libros/eliminar_libro/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Libro.query.get(libro.id))

    def test_flujo_busqueda_libros(self):
        self._crear_usuario(email="user@test.com", rol="usuario")
        self._login("user@test.com")

        self._crear_libro(isbn="9783161484100", titulo="Don Quijote")
        self._crear_libro(isbn="9783161484101", titulo="Cien Años de Soledad")

        response = self.client.get("/libros/buscar_libro?termino=Quijote")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/libros/buscar_libro?termino=Soledad")
        self.assertEqual(response.status_code, 200)

    def test_flujo_historial_prestamos(self):
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        libro = self._crear_libro()

        self._login("bib@test.com")
        self.client.post(
            f"/prestamos/prestar/{libro.id}",
            data={
                "usuario_id": usuario.id,
            },
            follow_redirects=True,
        )

        self._login("lector@test.com")
        response = self.client.get("/prestamos/historial")
        self.assertEqual(response.status_code, 200)

    def test_flujo_limite_prestamos(self):
        usuario = self._crear_usuario(email="lector@test.com", rol="usuario")
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")

        for i in range(3):
            libro = self._crear_libro(isbn=f"978316148410{i}", titulo=f"Libro {i}")
            self._login("bib@test.com")
            self.client.post(
                f"/prestamos/prestar/{libro.id}",
                data={
                    "usuario_id": usuario.id,
                },
                follow_redirects=True,
            )

        libro_extra = self._crear_libro(isbn="9783161484199", titulo="Libro Extra")
        self._login("bib@test.com")
        response = self.client.post(
            f"/prestamos/prestar/{libro_extra.id}",
            data={
                "usuario_id": usuario.id,
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_flujo_no_disponible_para_reserva(self):
        self._crear_usuario(email="lector@test.com", rol="usuario")
        libro = self._crear_libro(cantidad=0)

        self._login("lector@test.com")
        response = self.client.get(
            f"/prestamos/reservar/{libro.id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_flujo_importar_csv(self):
        self._crear_usuario(email="admin@test.com", rol="admin")
        self._login("admin@test.com")

        response = self.client.get("/libros/importar_datos")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
