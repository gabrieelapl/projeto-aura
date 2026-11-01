import app as app_module
from models import Usuario
from tests.conftest import criar_usuario


def test_paginas_publicas_carregam(client):
    for rota in ('/', '/login', '/cadastro'):
        assert client.get(rota).status_code == 200


def test_cadastro_cria_usuario_e_redireciona(client):
    resp = client.post('/cadastro', data={
        'nome': 'Ana', 'email': 'ana@teste.com', 'senha': 'senha123'})
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']
    usuario = Usuario.query.filter_by(email='ana@teste.com').first()
    assert usuario is not None
    assert usuario.senha != 'senha123'  # guardada como hash


def test_cadastro_rejeita_senha_curta(client):
    resp = client.post('/cadastro', data={
        'nome': 'Ana', 'email': 'ana@teste.com', 'senha': '123'})
    assert resp.status_code == 200
    assert Usuario.query.count() == 0


def test_cadastro_rejeita_email_duplicado(client):
    criar_usuario()
    resp = client.post('/cadastro', data={
        'nome': 'Outra', 'email': 'ana@teste.com', 'senha': 'senha123'})
    assert resp.status_code == 200
    assert Usuario.query.count() == 1


def test_login_correto_redireciona(client):
    criar_usuario()
    resp = client.post('/login', data={
        'email': 'ana@teste.com', 'senha': 'senha123'})
    assert resp.status_code == 302
    assert resp.headers['Location'] == '/'


def test_login_senha_errada_nao_entra(client):
    criar_usuario()
    resp = client.post('/login', data={
        'email': 'ana@teste.com', 'senha': 'errada'})
    assert resp.status_code == 200


def test_rota_protegida_redireciona_para_login(client):
    for rota in ('/perfil', '/funcionalidades', '/resumo'):
        resp = client.get(rota)
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']


def test_api_sem_login_retorna_401(client):
    resp = client.post('/api/resumo')
    assert resp.status_code == 401
    assert resp.get_json()['erro'] == 'Não autorizado'


def test_plano_pesquisa_valida_tamanho_da_pergunta(client_logado):
    resp = client_logado.post('/api/plano-pesquisa', json={'pergunta': 'curta'})
    assert resp.status_code == 400


def test_traduzir_texto_vazio(client_logado):
    resp = client_logado.post('/api/traduzir', json={'texto': '   '})
    assert resp.status_code == 400


def test_traduzir_usa_llm_mockado(client_logado, monkeypatch):
    monkeypatch.setattr(app_module, 'chamar_llm', lambda *a, **k: 'olá mundo')
    resp = client_logado.post('/api/traduzir', json={'texto': 'hello world'})
    assert resp.status_code == 200
    assert resp.get_json()['traducao'] == 'olá mundo'