import unittest
from main import create_app
from extensions import db
from src.models.models_usuario import Usuario
from flask_login import logout_user


class TestApp(unittest.TestCase):
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
        self, email="test@example.com", nombre="Test User", rol="usuario"
    ):
        usuario = Usuario(nombre=nombre, email=email, rol=rol)
        usuario.set_password("password123")
        usuario.email_confirmado = True
        usuario.token_confirmacion = None
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def _login(self, email="test@example.com", password="password123"):
        return self.client.post(
            "/auth/login",
            data={
                "email": email,
                "contrasena": password,
            },
            follow_redirects=True,
        )

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_login_GET(self):
        response = self.client.get("/auth/login")
        self.assertEqual(response.status_code, 200)

    def test_login_post(self):
        self._crear_usuario()
        response = self._login()
        self.assertEqual(response.status_code, 200)

    def test_registro_usuario(self):
        response = self.client.post(
            "/auth/registro",
            data={
                "nombre": "Usuario Test",
                "email": "test@example.com",
                "contrasena": "password123",
                "confirmar_contrasena": "password123",
                "rol": "usuario",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        usuario = Usuario.query.filter_by(email="test@example.com").first()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.nombre, "Usuario Test")

    def test_gestion_libros(self):
        self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self._login("bib@test.com")
        response = self.client.get("/libros/gestion_libros")
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self._crear_usuario(email="user@test.com")
        self._login("user@test.com")
        response = self.client.get("/auth/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_recordatorios(self):
        self._crear_usuario(email="user@test.com")
        self._login("user@test.com")
        response = self.client.get("/prestamos/recordatorios")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
