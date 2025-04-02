import pytest
from flask import url_for
from app import app, db
from modules.models import Usuario

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        db.drop_all()

def test_registro(client):
    response = client.post(url_for('registro'), data={
        'nombre': 'Usuario Test',
        'email': 'test@example.com',
        'contrasena': 'password123',
        'confirmar_contrasena': 'password123'
    })
    assert response.status_code == 302  # Redirige después de registro exitoso

def test_login(client):
    client.post(url_for('registro'), data={
        'nombre': 'Usuario Test',
        'email': 'test@example.com',
        'contrasena': 'password123',
        'confirmar_contrasena': 'password123'
    })
    response = client.post(url_for('login'), data={
        'email': 'test@example.com',
        'contrasena': 'password123'
    })
    assert response.status_code == 302  # Redirige después de inicio de sesión