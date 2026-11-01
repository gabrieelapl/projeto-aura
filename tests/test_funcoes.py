from datetime import datetime

from app import (
    formatar_data_pt, _iniciais, _ponto, _txt, _pag_vancouver,
    _cita_numero, _normalizar_ref, formatar_abnt,
)


def test_formatar_data_pt():
    assert formatar_data_pt(datetime(2026, 3, 5)) == '05 de março de 2026'


def test_iniciais():
    assert _iniciais('Ana Beatriz') == ['A', 'B']
    assert _iniciais('J.-P.') == ['J', 'P']


def test_ponto_adiciona_so_quando_falta():
    assert _ponto('Título') == 'Título.'
    assert _ponto('Título?') == 'Título?'
    assert _ponto('') == ''


def test_txt_ignora_listas_e_none():
    assert _txt(None) == ''
    assert _txt(['a']) == ''
    assert _txt(' 2020 ') == '2020'


def test_paginas_vancouver():
    assert _pag_vancouver('1234-1239') == '1234-9'
    assert _pag_vancouver('120-125') == '120-5'
    assert _pag_vancouver('89-102') == '89-102'
    assert _pag_vancouver('e123') == 'e123'


def test_cita_numero_com_faixa():
    texto = 'conforme estudos [1, 3-5]'
    assert _cita_numero(texto, 4) is True
    assert _cita_numero(texto, 2) is False


def test_normalizar_ref():
    bruta = {
        'autores': [{'sobrenome': 'Silva', 'nome': 'João Pedro'}],
        'titulo': 'Um título.',
        'fonte': 'Revista X',
        'tipo': 'ARTIGO',
        'ano': 2020,
        'paginas': '10–20',
        'doi': 'https://doi.org/10.1/abc',
    }
    ref = _normalizar_ref(bruta)
    assert ref['titulo'] == 'Um título'
    assert ref['tipo'] == 'artigo'
    assert ref['ano'] == '2020'
    assert ref['paginas'] == '10-20'
    assert ref['doi'] == '10.1/abc'


def test_formatar_abnt_artigo():
    ref = _normalizar_ref({
        'autores': [{'sobrenome': 'Silva', 'nome': 'João Pedro'}],
        'titulo': 'Um título',
        'fonte': 'Revista X',
        'tipo': 'artigo',
        'ano': '2020',
        'volume': '3',
    })
    resultado = formatar_abnt(ref)
    assert 'SILVA, J. P.' in resultado['texto']
    assert '<strong>Revista X</strong>' in resultado['html']