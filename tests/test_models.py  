from modules.models import Libro, Usuario, db

def test_validar_isbn():
    assert Libro.validar_isbn("1234567890") == True
    assert Libro.validar_isbn("1234567890123") == True
    assert Libro.validar_isbn("12345") == False

def test_validar_titulo_unico(app):
    with app.app_context():
        libro = Libro(isbn="1234567890", titulo="Libro Único", autor="Autor")
        db.session.add(libro)
        db.session.commit()
        assert Libro.validar_titulo("Libro Único") == False