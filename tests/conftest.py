import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'chave-de-teste'
os.environ['GROQ_API_KEY'] = 'chave-falsa'

import pytest 

import app as app_module  
from models import db, Usuario  


@pytest.fixture()
def flask_app():
    app_module.app.config['TESTING'] = True
    with app_module.app.app_context():
        db.create_all()
        yield app_module.app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


def criar_usuario(email='ana@teste.com', senha='senha123'):
    senha_hash = app_module.bcrypt.generate_password_hash(senha).decode('utf-8')
    usuario = Usuario(nome='Ana', email=email, senha=senha_hash)
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture()
def client_logado(client):
    criar_usuario()
    client.post('/login', data={'email': 'ana@teste.com', 'senha': 'senha123'})
    return client