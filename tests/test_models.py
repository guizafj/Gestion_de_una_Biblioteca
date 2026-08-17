import unittest
from unittest.mock import patch
from main import create_app
from extensions import db
from src.models.models_libro import Libro
from src.models.models_usuario import Usuario
from src.models.models_prestamo import Prestamo
from src.models.models_reserva import Reserva
from datetime import datetime, timezone, timedelta


def _dt_naive(*args, **kwargs):
    return datetime(*args, **kwargs)


class TestLibroModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.rollback()

    def _crear_libro(self, isbn="9783161484100", titulo="Test Book", **kwargs):
        libro = Libro(
            isbn=isbn,
            titulo=titulo,
            autor=kwargs.get("autor", "Autor Test"),
            editorial=kwargs.get("editorial", "Editorial Test"),
            genero=kwargs.get("genero", "Genero Test"),
            cantidad=kwargs.get("cantidad", 5),
        )
        db.session.add(libro)
        db.session.commit()
        return libro

    # --- ISBN validation ---

    def test_validar_isbn13_valido(self):
        isbn = Libro.validar_isbn("9783161484100")
        self.assertEqual(isbn, "9783161484100")

    def test_validar_isbn10_valido(self):
        isbn = Libro.validar_isbn("0306406152")
        self.assertEqual(isbn, "0306406152")

    def test_validar_isbn10_con_x(self):
        isbn = Libro.validar_isbn("0-8044-2957-X")
        self.assertEqual(isbn, "080442957X")

    def test_validar_isbn_vacio(self):
        with self.assertRaises(ValueError):
            Libro.validar_isbn("")

    def test_validar_isbn_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            Libro.validar_isbn("abc1234567890")

    def test_validar_isbn_digito_invalido(self):
        with self.assertRaises(ValueError):
            Libro.validar_isbn("9783161484101")

    def test_validar_isbn_largo_invalido(self):
        with self.assertRaises(ValueError):
            Libro.validar_isbn("123456789")

    def test_validar_isbn_duplicado(self):
        self._crear_libro(isbn="9783161484100")
        with self.assertRaises(ValueError):
            Libro.validar_isbn("9783161484100")

    def test_validar_isbn_duplicado_mismo_libro(self):
        libro = self._crear_libro(isbn="9783161484100")
        isbn = Libro.validar_isbn("9783161484100", libro_id=libro.id)
        self.assertEqual(isbn, "9783161484100")

    # --- Titulo validation ---

    def test_validar_titulo_valido(self):
        titulo = Libro.validar_titulo("El Principito")
        self.assertEqual(titulo, "El Principito")

    def test_validar_titulo_vacio(self):
        with self.assertRaises(ValueError):
            Libro.validar_titulo("")

    def test_validar_titulo_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            Libro.validar_titulo("Libro123!")

    def test_validar_titulo_duplicado(self):
        self._crear_libro(titulo="Unico")
        with self.assertRaises(ValueError):
            Libro.validar_titulo("Unico")

    def test_validar_titulo_duplicado_mismo_libro(self):
        libro = self._crear_libro(titulo="Unico")
        titulo = Libro.validar_titulo("Unico", libro_id=libro.id)
        self.assertEqual(titulo, "Unico")

    # --- Autor validation ---

    def test_validar_autor_valido(self):
        autor = Libro.validar_autor("Gabriel García Márquez")
        self.assertEqual(autor, "Gabriel García Márquez")

    def test_validar_autor_vacio(self):
        with self.assertRaises(ValueError):
            Libro.validar_autor("")

    def test_validar_autor_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            Libro.validar_autor("Autor123!")

    # --- Editorial validation ---

    def test_validar_editorial_valida(self):
        ed = Libro.validar_editorial("Editorial Sudamericana")
        self.assertEqual(ed, "Editorial Sudamericana")

    def test_validar_editorial_vacia(self):
        with self.assertRaises(ValueError):
            Libro.validar_editorial("")

    # --- Genero validation ---

    def test_validar_genero_valido(self):
        gen = Libro.validar_genero("Ficción")
        self.assertEqual(gen, "Ficción")

    def test_validar_genero_vacio(self):
        with self.assertRaises(ValueError):
            Libro.validar_genero("")

    # --- Cantidad validation ---

    def test_validar_cantidad_valida(self):
        cant = Libro.validar_cantidad(5)
        self.assertEqual(cant, 5)

    def test_validar_cantidad_string(self):
        cant = Libro.validar_cantidad("3")
        self.assertEqual(cant, 3)

    def test_validar_cantidad_cero(self):
        with self.assertRaises(ValueError):
            Libro.validar_cantidad(0)

    def test_validar_cantidad_negativa(self):
        with self.assertRaises(ValueError):
            Libro.validar_cantidad(-1)

    def test_validar_cantidad_no_numero(self):
        with self.assertRaises(ValueError):
            Libro.validar_cantidad("abc")

    def test_validar_cantidad_vacia(self):
        with self.assertRaises(ValueError):
            Libro.validar_cantidad("")

    # --- Propiedades y métodos ---

    def test_esta_disponible(self):
        libro = self._crear_libro(cantidad=3)
        self.assertTrue(libro.esta_disponible)

    def test_no_esta_disponible(self):
        libro = self._crear_libro(cantidad=0)
        self.assertFalse(libro.esta_disponible)

    def test_reducir_cantidad(self):
        libro = self._crear_libro(cantidad=3)
        libro.reducir_cantidad()
        self.assertEqual(libro.cantidad, 2)

    def test_reducir_cantidad_a_cero(self):
        libro = self._crear_libro(cantidad=1)
        libro.reducir_cantidad()
        self.assertEqual(libro.cantidad, 0)

    def test_reducir_cantidad_sin_ejemplares(self):
        libro = self._crear_libro(cantidad=0)
        with self.assertRaises(ValueError):
            libro.reducir_cantidad()

    def test_incrementar_cantidad(self):
        libro = self._crear_libro(cantidad=2)
        libro.incrementar_cantidad()
        self.assertEqual(libro.cantidad, 3)

    def test_contar_libros(self):
        self._crear_libro(isbn="9783161484100", titulo="A")
        self._crear_libro(isbn="9783161484101", titulo="B")
        self.assertEqual(Libro.contar_libros(), 2)

    def test_repr(self):
        libro = self._crear_libro(titulo="Mi Libro")
        self.assertIn("Mi Libro", repr(libro))


class TestUsuarioModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.rollback()

    def _crear_usuario(
        self, email="test@example.com", nombre="Test User", rol="usuario"
    ):
        usuario = Usuario(nombre=nombre, email=email, rol=rol)
        usuario.set_password("password123")
        db.session.add(usuario)
        db.session.commit()
        return usuario

    # --- Password ---

    def test_set_and_check_password(self):
        usuario = self._crear_usuario()
        self.assertTrue(usuario.check_password("password123"))
        self.assertFalse(usuario.check_password("wrongpassword"))

    def test_contrasena_hash_no_accesible(self):
        usuario = self._crear_usuario()
        with self.assertRaises(AttributeError):
            _ = usuario.contrasena_hash

    # --- Validaciones ---

    def test_validar_email_invalido(self):
        with self.assertRaises(ValueError):
            Usuario(nombre="Test", email="invalid-email", rol="usuario")

    def test_validar_email_duplicado(self):
        self._crear_usuario(email="dup@example.com")
        with self.assertRaises(ValueError):
            self._crear_usuario(email="dup@example.com")

    def test_validar_nombre_largo(self):
        with self.assertRaises(ValueError):
            self._crear_usuario(nombre="A" * 101)

    def test_validar_nombre_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            self._crear_usuario(nombre="Nombre123!")

    # --- Roles ---

    def test_roles(self):
        usuario = self._crear_usuario(rol="usuario")
        self.assertTrue(usuario.es_usuario_regular())
        self.assertFalse(usuario.es_admin())
        self.assertFalse(usuario.es_bibliotecario())

    def test_rol_admin(self):
        admin = self._crear_usuario(email="admin@test.com", rol="admin")
        self.assertTrue(admin.es_admin())

    def test_rol_bibliotecario(self):
        bib = self._crear_usuario(email="bib@test.com", rol="bibliotecario")
        self.assertTrue(bib.es_bibliotecario())

    def test_tiene_rol(self):
        usuario = self._crear_usuario(rol="usuario")
        self.assertTrue(usuario.tiene_rol("usuario"))
        self.assertFalse(usuario.tiene_rol("admin"))

    # --- Token confirmacion ---

    def test_generar_token_confirmacion(self):
        usuario = self._crear_usuario()
        token = usuario.generar_token_confirmacion()
        self.assertIsNotNone(token)
        self.assertEqual(usuario.token_confirmacion, token)
        self.assertIsNotNone(usuario.token_expiracion)

    def test_confirmar_email(self):
        usuario = self._crear_usuario()
        usuario.generar_token_confirmacion()
        usuario.confirmar_email()
        self.assertTrue(usuario.email_confirmado)
        self.assertIsNone(usuario.token_confirmacion)
        self.assertIsNone(usuario.token_expiracion)

    def test_confirmar_email_token_expirado(self):
        usuario = self._crear_usuario()
        usuario.generar_token_confirmacion()
        with patch("src.models.models_usuario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2099, 1, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            usuario.token_expiracion = datetime(2020, 1, 1)
            db.session.commit()
            with self.assertRaises(ValueError):
                usuario.confirmar_email()

    def test_confirmar_email_sin_token(self):
        usuario = self._crear_usuario()
        with self.assertRaises(ValueError):
            usuario.confirmar_email()

    # --- Bloqueo de cuenta ---

    def test_bloquear_cuenta(self):
        usuario = self._crear_usuario()
        usuario.intentos_fallidos = 5
        with patch("src.models.models_usuario.datetime") as mock_dt:
            now = datetime(2025, 6, 1, 12, 0, 0)
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            usuario.bloquear_cuenta()
            self.assertIsNotNone(usuario.cuenta_bloqueada_hasta)
            self.assertTrue(usuario.esta_bloqueada())

    def test_no_bloqueada_normalmente(self):
        usuario = self._crear_usuario()
        with patch("src.models.models_usuario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            self.assertFalse(usuario.esta_bloqueada())

    def test_limitador_inicio(self):
        usuario = self._crear_usuario()
        usuario.intentos_fallidos = 5
        resultado = usuario.limitador_inicio()
        self.assertTrue(resultado)

    def test_limitador_inicio_no_bloquea(self):
        usuario = self._crear_usuario()
        usuario.intentos_fallidos = 3
        resultado = usuario.limitador_inicio()
        self.assertFalse(resultado)

    def test_resetear_intentos(self):
        usuario = self._crear_usuario()
        usuario.intentos_fallidos = 4
        usuario.resetear_intentos_fallidos()
        self.assertEqual(usuario.intentos_fallidos, 0)

    # --- Correo confirmado ---

    def test_correo_confirmado_true(self):
        usuario = self._crear_usuario()
        usuario.email_confirmado = True
        usuario.token_confirmacion = None
        db.session.commit()
        self.assertTrue(usuario.correo_confirmado())

    def test_correo_confirmado_false(self):
        usuario = self._crear_usuario()
        self.assertFalse(usuario.correo_confirmado())

    # --- Reservas ---

    def test_tiene_reservas_activas_false(self):
        usuario = self._crear_usuario()
        self.assertFalse(usuario.tiene_reservas_activas())

    def test_obtener_estadisticas_reservas_vacio(self):
        usuario = self._crear_usuario()
        stats = usuario.obtener_estadisticas_reservas()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["pendientes"], 0)

    def test_repr(self):
        usuario = self._crear_usuario(nombre="Juan")
        self.assertIn("Juan", repr(usuario))


class TestPrestamoModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.libro = Libro(
            isbn="9783161484100",
            titulo="Libro Test",
            autor="Autor",
            editorial="Editorial",
            genero="Genero",
            cantidad=5,
        )
        db.session.add(self.libro)
        db.session.commit()

        self.usuario = Usuario(nombre="Usuario Test", email="u@test.com", rol="usuario")
        self.usuario.set_password("password123")
        db.session.add(self.usuario)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def _crear_prestamo(self, usuario=None, libro=None):
        prestamo = Prestamo(
            libro_id=(libro or self.libro).id,
            usuario_id=(usuario or self.usuario).id,
        )
        db.session.add(prestamo)
        db.session.commit()
        return prestamo

    def test_crear_prestamo(self):
        prestamo = self._crear_prestamo()
        self.assertEqual(prestamo.estado, "activo")
        self.assertIsNone(prestamo.fecha_devolucion)

    def test_duracion_prestamo(self):
        prestamo = self._crear_prestamo()
        with patch("src.models.models_prestamo.datetime") as mock_dt:
            mock_dt.now.return_value = prestamo.fecha_prestamo
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            duracion = prestamo.duracion_prestamo()
            self.assertEqual(duracion, 0)

    def test_calcular_fecha_vencimiento(self):
        prestamo = self._crear_prestamo()
        vencimiento = prestamo.calcular_fecha_vencimiento(dias_prestamo=14)
        esperado = prestamo.fecha_prestamo + timedelta(days=14)
        self.assertEqual(vencimiento.date(), esperado.date())

    def test_esta_vencido_no(self):
        prestamo = self._crear_prestamo()
        with patch("src.models.models_prestamo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            self.assertFalse(prestamo.esta_vencido())

    def test_esta_vencido_si(self):
        prestamo = self._crear_prestamo()
        prestamo.fecha_prestamo = datetime(2025, 1, 1)
        db.session.commit()
        with patch("src.models.models_prestamo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 12, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            self.assertTrue(prestamo.esta_vencido())

    def test_marcar_como_devuelto(self):
        prestamo = self._crear_prestamo()
        cantidad_inicial = self.libro.cantidad
        prestamo.marcar_como_devuelto()
        self.assertEqual(prestamo.estado, "devuelto")
        self.assertIsNotNone(prestamo.fecha_devolucion)
        self.assertEqual(self.libro.cantidad, cantidad_inicial + 1)

    def test_marcar_como_devuelto_ya_devuelto(self):
        prestamo = self._crear_prestamo()
        prestamo.marcar_como_devuelto()
        with self.assertRaises(ValueError):
            prestamo.marcar_como_devuelto()

    def test_prestamos_activos(self):
        self._crear_prestamo()
        self._crear_prestamo()
        self.assertEqual(Prestamo.prestamos_activos(self.usuario.id), 2)

    def test_validar_prestamo_ok(self):
        Prestamo.validar_prestamo(self.usuario.id)

    def test_validar_prestamo_limite(self):
        for _ in range(3):
            self._crear_prestamo()
        with self.assertRaises(ValueError):
            Prestamo.validar_prestamo(self.usuario.id)

    def test_calcular_penalizacion_sin_retraso(self):
        prestamo = self._crear_prestamo()
        with patch("src.models.models_prestamo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            self.assertEqual(prestamo.calcular_penalizacion(), 0)

    def test_calcular_penalizacion_con_retraso(self):
        prestamo = self._crear_prestamo()
        prestamo.fecha_prestamo = datetime(2025, 1, 1)
        db.session.commit()
        with patch("src.models.models_prestamo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 12, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            penalizacion = prestamo.calcular_penalizacion(tarifa_por_dia=1)
            self.assertGreater(penalizacion, 0)

    def test_repr(self):
        prestamo = self._crear_prestamo()
        self.assertIn("Libro Test", repr(prestamo))


class TestReservaModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.libro = Libro(
            isbn="9783161484100",
            titulo="Libro Reserva",
            autor="Autor",
            editorial="Editorial",
            genero="Genero",
            cantidad=3,
        )
        db.session.add(self.libro)
        db.session.commit()

        self.usuario = Usuario(
            nombre="Usuario Reserva", email="r@test.com", rol="usuario"
        )
        self.usuario.set_password("password123")
        db.session.add(self.usuario)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_crear_reserva(self):
        reserva = Reserva(libro_id=self.libro.id, usuario_id=self.usuario.id)
        db.session.add(reserva)
        db.session.commit()
        self.assertEqual(reserva.estado, "pendiente")
        self.assertIsNotNone(reserva.fecha_reserva)

    def test_validar_reserva_ok(self):
        Reserva.validar_reserva(self.libro.id)

    def test_validar_reserva_libro_no_existe(self):
        with self.assertRaises(ValueError):
            Reserva.validar_reserva(9999)

    def test_validar_reserva_libro_no_disponible(self):
        self.libro.cantidad = 0
        db.session.commit()
        with self.assertRaises(ValueError):
            Reserva.validar_reserva(self.libro.id)

    def test_expirar_reservas(self):
        reserva = Reserva(libro_id=self.libro.id, usuario_id=self.usuario.id)
        reserva.fecha_reserva = datetime.now(timezone.utc) - timedelta(days=10)
        db.session.add(reserva)
        db.session.commit()

        Reserva.expirar_reservas()
        reserva_actualizada = Reserva.query.get(reserva.id)
        self.assertEqual(reserva_actualizada.estado, "rechazada")

    def test_expirar_reservas_no_expira(self):
        reserva = Reserva(libro_id=self.libro.id, usuario_id=self.usuario.id)
        db.session.add(reserva)
        db.session.commit()

        Reserva.expirar_reservas()
        reserva_actualizada = Reserva.query.get(reserva.id)
        self.assertEqual(reserva_actualizada.estado, "pendiente")

    def test_repr(self):
        reserva = Reserva(libro_id=self.libro.id, usuario_id=self.usuario.id)
        db.session.add(reserva)
        db.session.commit()
        self.assertIn("Libro Reserva", repr(reserva))


if __name__ == "__main__":
    unittest.main()
