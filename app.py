from flask import Flask, render_template, request, redirect, session, url_for, send_file
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db, Usuario, Projeto, Artigo
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import requests
from huggingface_hub import InferenceClient
import pymupdf as fitz
from flask_session import Session
from flask_bcrypt import Bcrypt
import json
import re
from html import escape as html_escape
from pypdf import PdfReader

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = os.getenv('SECRET_KEY')

# Banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Flask session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), '.flask_session')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

Session(app)

# Pastas de uploads
UPLOAD_FOLDER = os.path.join('static', 'img', 'fotos')
ARTIGOS_FOLDER = os.path.join('static', 'uploads', 'artigos')
AUDIO_FOLDER = os.path.join('static', 'uploads', 'audio')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ARTIGOS_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Formata meses em português
def formatar_data_pt(data_obj):
    meses = {
        'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
        'April': 'abril', 'May': 'maio', 'June': 'junho',
        'July': 'julho', 'August': 'agosto', 'September': 'setembro',
        'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
    }
    data_str = data_obj.strftime('%d de %B de %Y')
    for en, pt in meses.items():
        data_str = data_str.replace(en, pt)
    return data_str


# Hugging face hub + Groq
MODELO_LLM = 'openai/gpt-oss-120b'

def chamar_llm(messages, max_tokens=1000, temperature=0.3):
    """Chama o LLM usando a biblioteca huggingface_hub com a chave da Groq.

    Retorna o texto da resposta. Levanta exceção em caso de erro.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise RuntimeError('GROQ_API_KEY não configurada no arquivo .env')

    client = InferenceClient(api_key=api_key, provider='groq')
    result = client.chat_completion(
        messages=messages,
        model=MODELO_LLM,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    texto = (result.choices[0].message.content or '').strip()
    if not texto:
        raise RuntimeError('O modelo retornou uma resposta vazia. Tente novamente.')
    return texto


# --- ROTAS ---
@app.route('/')
def index():
    projetos_formatados = []
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario:
            projetos_db = Projeto.query.filter_by(usuario_id=usuario.id).all()

            for p in projetos_db:
                artigos_list = [{
                    'nome': a.nome,
                    'status': a.status,
                    'data': a.data,
                    'caminho': a.caminho
                } for a in p.artigos]

                projetos_formatados.append({
                    'id': p.id,
                    'nome': p.nome,
                    'data': p.data,
                    'total': len(artigos_list),
                    'incluido': sum(1 for a in artigos_list if a['status'] == 'incluido'),
                    'excluido': sum(1 for a in artigos_list if a['status'] == 'excluido'),
                    'pendente': sum(1 for a in artigos_list if a['status'] == 'pendente'),
                    'artigos': artigos_list
                })

    return render_template('index.html', projetos=projetos_formatados)

# ROTA DE CADASTRO
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not nome or not email or not senha:
            return render_template('cadastro.html', erro='Preencha todos os campos.')
        if len(senha) < 6:
            return render_template('cadastro.html', erro='A senha deve ter pelo menos 6 caracteres.')
        if Usuario.query.filter_by(email=email).first():
            return render_template('cadastro.html', erro='Este e-mail já está cadastrado.')

        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
        novo = Usuario(nome=nome, email=email, senha=senha_hash)
        db.session.add(novo)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('cadastro.html')

# ROTA DE LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not email or not senha:
            return render_template('login.html', erro='Preencha todos os campos.')

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not bcrypt.check_password_hash(usuario.senha, senha):
            return render_template('login.html', erro='E-mail ou senha incorretos.')

        session['usuario_id'] = usuario.id
        session['usuario'] = usuario.email
        session['nome'] = usuario.nome
        session['bio'] = usuario.bio or ''
        session['foto'] = usuario.foto or ''
        session['membro_desde'] = formatar_data_pt(usuario.data_cadastro)

        return redirect(url_for('index'))

    return render_template('login.html')

# ROTA DE LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ROTA DE PERFIL
@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('perfil.html')

# ROTA DE EDITAR PERFIL
@app.route('/editarPerfil', methods=['GET', 'POST'])
def editarPerfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        bio = request.form.get('bio', '').strip()

        if not nome:
            return render_template('editarPerfil.html', erro='O nome não pode estar vazio.')

        usuario.nome = nome
        usuario.bio = bio
        session['nome'] = nome
        session['bio'] = bio

        foto = request.files.get('foto')
        if foto and foto.filename:
            nome_arquivo = f"{session['usuario_id']}_{secure_filename(foto.filename)}"
            foto.save(os.path.join(UPLOAD_FOLDER, nome_arquivo))
            usuario.foto = nome_arquivo
            session['foto'] = nome_arquivo

        db.session.commit()
        return redirect(url_for('perfil'))

    return render_template('editarPerfil.html')

# ROTA PARA ALTERAR SENHA
@app.route('/alterar-senha', methods=['GET', 'POST'])
def alterarSenha():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '').strip()
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()

        if not bcrypt.check_password_hash(usuario.senha, senha_atual):
            return render_template('alterarSenha.html', erro='Senha atual incorreta.')
        if nova_senha != confirmar_senha:
            return render_template('alterarSenha.html', erro='As senhas não coincidem.')
        if len(nova_senha) < 6:
            return render_template('alterarSenha.html', erro='A nova senha deve ter pelo menos 6 caracteres.')

        usuario.senha = bcrypt.generate_password_hash(
            nova_senha).decode('utf-8')
        db.session.commit()
        return render_template('alterarSenha.html', sucesso='Senha alterada com sucesso!')

    return render_template('alterarSenha.html')

# ROTA PARA EXCLUIR CONTA
@app.route('/excluir-conta')
def excluirConta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    db.session.delete(usuario)
    db.session.commit()
    session.clear()
    return redirect(url_for('cadastro'))

# ROTA DE UPLOAD
@app.route('/upload', methods=['POST'])
def upload():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    artigo = request.files.get('artigo')
    nome_artigo = request.form.get('artigo_nome', '').strip()
    tamanho = request.form.get('artigo_tamanho', '')
    projeto_tipo = request.form.get('projeto_tipo', 'novo')
    projeto_id = request.form.get('projeto_id', '').strip()
    nome_novo = request.form.get('projeto_novo', '').strip()

    caminho = None
    if artigo and artigo.filename:
        nome_exibir = nome_artigo or secure_filename(artigo.filename)
        nome_arquivo = secure_filename(artigo.filename)
        pasta = os.path.join(ARTIGOS_FOLDER, str(session['usuario_id']))
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_arquivo)
        artigo.save(caminho)
        session['artigo_caminho'] = caminho
        session['artigo_nome'] = nome_exibir
        session['artigo_meta'] = f'{tamanho} · PDF'
    else:
        nome_exibir = nome_artigo or 'Artigo'

    data_hoje = formatar_data_pt(datetime.now())

    if projeto_tipo == 'novo':
        nome_projeto = nome_novo if nome_novo else 'Novo Projeto'
        novo_proj_id = str(uuid.uuid4())[:8]

        novo_projeto = Projeto(
            id=novo_proj_id,
            nome=nome_projeto,
            data=data_hoje,
            usuario_id=session['usuario_id']
        )
        db.session.add(novo_projeto)
        db.session.commit()

        novo_artigo_db = Artigo(
            nome=nome_exibir,
            status='pendente',
            data=data_hoje,
            caminho=caminho,
            projeto_id=novo_proj_id
        )
        db.session.add(novo_artigo_db)
        db.session.commit()
    else:
        projeto_existente = Projeto.query.get(projeto_id)
        if projeto_existente and projeto_existente.usuario_id == session['usuario_id']:
            novo_artigo_db = Artigo(
                nome=nome_exibir,
                status='pendente',
                data=data_hoje,
                caminho=caminho,
                projeto_id=projeto_id
            )
            db.session.add(novo_artigo_db)
            db.session.commit()

    return redirect(url_for('funcionalidades'))

# ROTA PARA RENOMEAR PROJETO
@app.route('/renomear-projeto/<id>', methods=['POST'])
def renomear_projeto(id):
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401
    data = request.get_json()
    projeto = Projeto.query.get(id)
    if projeto and projeto.usuario_id == session['usuario_id']:
        projeto.nome = data.get('nome', projeto.nome)
        db.session.commit()
        return {'ok': True}
    return {'erro': 'Projeto não encontrado'}, 404

# ROTA PARA DELETAR PROJETO
@app.route('/deletar-projeto/<id>', methods=['POST'])
def deletar_projeto(id):
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401
    projeto = Projeto.query.get(id)
    if projeto and projeto.usuario_id == session['usuario_id']:
        db.session.delete(projeto)
        db.session.commit()
        return {'ok': True}
    return {'erro': 'Projeto não encontrado'}, 404


@app.route('/projeto/<id>')
def projeto(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    p = Projeto.query.get(id)
    if not p or p.usuario_id != session['usuario_id']:
        return redirect(url_for('index'))

    artigos_list = [{'nome': a.nome, 'status': a.status,
                     'data': a.data, 'caminho': a.caminho} for a in p.artigos]
    proj_dict = {
        'id': p.id,
        'nome': p.nome,
        'data': p.data,
        'total': len(artigos_list),
        'artigos': artigos_list
    }
    return render_template('projeto.html', projeto=proj_dict)


@app.route('/abrir-artigo/<projeto_id>/<int:artigo_idx>')
def abrir_artigo(projeto_id, artigo_idx):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    p = Projeto.query.get(projeto_id)
    if not p or p.usuario_id != session['usuario_id'] or artigo_idx >= len(p.artigos):
        return redirect(url_for('index'))

    artigo = p.artigos[artigo_idx]
    session['artigo_nome'] = artigo.nome
    session['artigo_meta'] = f"{artigo.data} · PDF"
    session['artigo_caminho'] = artigo.caminho or ''
    session.modified = True

    return redirect(url_for('funcionalidades'))

# ROTA DE FUNCIONALIDADES
@app.route('/funcionalidades')
def funcionalidades():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    return render_template('funcionalidades.html',
                           artigo_nome=session.get(
                               'artigo_nome', 'Artigo científico'),
                           artigo_meta=session.get('artigo_meta', 'Arquivo carregado'))

# ROTA PARA VER O PDF
@app.route('/ver-pdf')
def ver_pdf():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    caminho = session.get('artigo_caminho')
    if not caminho or not os.path.exists(caminho):
        return 'Arquivo não encontrado', 404

    return send_file(caminho, mimetype='application/pdf')

# ROTA DE GERAR RESUMO
@app.route('/resumo')
def resumo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('resumo.html')

# API PARA GERAR RESUMO
@app.route('/api/resumo', methods=['POST'])
def api_resumo():
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    caminho = session.get('artigo_caminho')
    if not caminho or not os.path.exists(caminho):
        return {'erro': 'Nenhum artigo encontrado. Faça o upload novamente.'}, 400

    try:
        doc = fitz.open(caminho)
        texto = ' '.join([pagina.get_text() for pagina in doc])
        doc.close()
        texto = texto[:4000]
    except Exception as e:
        return {'erro': f'Erro ao ler o PDF: {str(e)}'}, 500

    if not texto.strip():
        return {'erro': 'Não foi possível extrair texto do PDF.'}, 400

    messages = [
        {
            'role': 'system',
            'content': (
                'Você é um assistente acadêmico especializado em revisão sistemática. '
                'Leia o artigo científico completo e gere um resumo fluido e contínuo em português, '
                'sem dividir em tópicos ou seções. O resumo deve apresentar de forma integrada: '
                'o contexto e objetivo do estudo, a metodologia utilizada, os principais resultados '
                'encontrados e as conclusões dos autores.'
            )
        },
        {
            'role': 'user',
            'content': f'Resuma o seguinte artigo científico:\n\n{texto}'
        }
    ]

    try:
        resumo_texto = chamar_llm(messages, max_tokens=2000, temperature=0.3)
        session['resumo_gerado'] = resumo_texto
        return {'resumo': resumo_texto}
    except Exception as e:
        return {'erro': f'Erro ao gerar resumo: {str(e)}'}, 500

# ROTA E API DE ÁUDIO
@app.route('/audio')
def audio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template(
        'audio.html',
        artigo_nome=session.get('artigo_nome', 'Resumo do artigo'))


@app.route('/api/audio', methods=['POST'])
def api_audio():
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    resumo = session.get('resumo_gerado')
    if not resumo:
        return {'erro': 'Nenhum resumo encontrado. Gere o resumo primeiro.'}, 400

    api_key = os.getenv('ELEVENLABS_API_KEY')
    voice_id = 'pNInz6obpgDQGcFmaJgB'
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': resumo,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            return {'erro': f'Erro da API: {resp.status_code} - {resp.text[:300]}'}, 500

        nome_audio = f"audio_{session['usuario_id']}.mp3"
        caminho = os.path.join(AUDIO_FOLDER, nome_audio)
        with open(caminho, 'wb') as f:
            f.write(resp.content)

        return {'audio_url': f'/static/uploads/audio/{nome_audio}'}
    except Exception as e:
        return {'erro': f'Erro ao gerar áudio: {str(e)}'}, 500

# ROTAS E API CITAÇÃO
@app.route('/citacoes')
def citacoes():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('citacoes.html')

MAX_REFERENCIAS = 20
MAX_CHARS_REFERENCIAS = 7000
RE_TITULO_REFERENCIAS = re.compile(
    r'^\s*(?:\d+\.?\s*)?(references|referências|referencias|bibliography|'
    r'bibliografia|literatura citada)\s*:?\s*$',
    re.I | re.M)

def extrair_paginas_pdf(caminho):
    try:
        doc = fitz.open(caminho)

        paginas = []

        for pagina in doc:
            paginas.append(pagina.get_text("text"))

        doc.close()

        return paginas

    except Exception as erro:
        print("Erro no PyMuPDF:", erro)

        try:
            leitor = PdfReader(caminho, strict=False)

            paginas = [
                pagina.extract_text() or ""
                for pagina in leitor.pages
            ]

            return paginas

        except Exception as erro_pdf:
            print("Erro no pypdf:", erro_pdf)
            raise Exception(
                "Não foi possível extrair o texto deste PDF."
            )
            
def separar_corpo_e_referencias(caminho):

    paginas = extrair_paginas_pdf(caminho)

    achado = None

    for i, texto in enumerate(paginas):
        for m in RE_TITULO_REFERENCIAS.finditer(texto):
            achado = (i, m.start())

    if not achado:
        return [(i + 1, t) for i, t in enumerate(paginas)], None

    i, pos = achado

    corpo = [
        (n + 1, paginas[n])
        for n in range(i)
    ]

    corpo.append((i + 1, paginas[i][:pos]))

    refs = paginas[i][pos:] + '\n' + '\n'.join(paginas[i + 1:])

    return corpo, refs


def extrair_referencias_llm(texto_refs):
    messages = [
        {
            'role': 'system',
            'content': (
                'Você extrai dados bibliográficos de listas de referências de artigos '
                'científicos. Responda APENAS com um objeto JSON válido, sem markdown, '
                f'no formato {{"referencias": [...]}} com no máximo {MAX_REFERENCIAS} '
                'itens, na ordem em que aparecem. Cada item deve ter exatamente estas '
                'chaves: "autores" (lista de objetos {"sobrenome": "", "nome": ""}, onde '
                '"nome" são os prenomes ou iniciais exatamente como aparecem), "titulo", '
                '"fonte" (nome do periódico, editora ou site), "tipo" ("artigo", "livro" '
                'ou "outro"), "ano", "volume", "numero", "paginas" (ex.: "89-102") e '
                '"doi". Use string vazia quando a informação não estiver na referência. '
                'Não invente dados e não corrija o texto. Se o autor for uma organização, '
                'coloque o nome dela em "sobrenome" e deixe "nome" vazio.'
            )
        },
        {
            'role': 'user',
            'content': f'Referências do artigo:\n\n{texto_refs}'
        }
    ]
    bruto = chamar_llm(messages, max_tokens=4500, temperature=0.1)
    achado = re.search(r'\{.*\}', bruto, re.S)
    if not achado:
        raise ValueError('formato inesperado')
    dados = json.loads(achado.group(0))
    refs = dados.get('referencias', [])
    if not isinstance(refs, list):
        raise ValueError('formato inesperado')
    return refs[:MAX_REFERENCIAS]


def _txt(v):
    if v is None or isinstance(v, (list, dict)):
        return ''
    return str(v).strip()


def _normalizar_ref(r):
    autores = []
    for a in r.get('autores') or []:
        if isinstance(a, dict):
            sob, nome = _txt(a.get('sobrenome')), _txt(a.get('nome'))
        else:
            sob, nome = _txt(a), ''
        if sob:
            autores.append({'sobrenome': sob, 'nome': nome})
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', _txt(r.get('doi')), flags=re.I)
    return {
        'autores': autores,
        'titulo': _txt(r.get('titulo')).rstrip('.'),
        'fonte': _txt(r.get('fonte')),
        'tipo': _txt(r.get('tipo')).lower(),
        'ano': _txt(r.get('ano')),
        'volume': _txt(r.get('volume')),
        'numero': _txt(r.get('numero')),
        'paginas': _txt(r.get('paginas')).replace('–', '-').replace('—', '-'),
        'doi': doi,
    }


def _iniciais(nome):
    partes = [p for p in re.split(r'[\s.\-]+', nome) if p]
    return [p[0].upper() for p in partes]


def _ponto(s):
    s = s.strip()
    return s if not s or s[-1] in '.?!' else s + '.'


def _montar(segmentos):
    segmentos = [(t, e) for t, e in segmentos if t]
    if segmentos:
        t, e = segmentos[-1]
        segmentos[-1] = (t.rstrip(), e)
    plano = ''.join(t for t, _ in segmentos)
    html = ''.join(
        f'<{e}>{html_escape(t)}</{e}>' if e else html_escape(t)
        for t, e in segmentos)
    return {'texto': plano, 'html': html}


def _pag_vancouver(p):
    m = re.match(r'^(\d+)\s*-\s*(\d+)$', p)
    if not m:
        return p
    a, b = m.group(1), m.group(2)
    if len(a) != len(b):
        return p
    comum = 0
    while comum < len(a) - 1 and a[comum] == b[comum]:
        comum += 1
    return f'{a}-{b[comum:]}'


def formatar_abnt(r):
    def nome(a):
        ini = ' '.join(i + '.' for i in _iniciais(a['nome']))
        return f"{a['sobrenome'].upper()}, {ini}" if ini else a['sobrenome'].upper()

    aut = r['autores']
    if len(aut) > 3:
        autores = nome(aut[0]) + ' et al.'
    else:
        autores = '; '.join(nome(a) for a in aut)

    seg = []
    if autores:
        seg.append((_ponto(autores) + ' ', None))
    seg.append((_ponto(r['titulo']) + ' ', None))

    if r['tipo'] == 'artigo' and r['fonte']:
        seg.append((r['fonte'], 'strong'))
        extras = []
        if r['volume']:
            extras.append(f"v. {r['volume']}")
        if r['numero']:
            extras.append(f"n. {r['numero']}")
        if r['paginas']:
            extras.append(f"p. {r['paginas']}")
        if r['ano']:
            extras.append(r['ano'])
        seg.append((''.join(', ' + e for e in extras) + '.', None))
    else:
        resto = ', '.join(x for x in [r['fonte'], r['ano']] if x)
        seg.append((_ponto(resto) if resto else '', None))

    if r['doi']:
        seg.append((f" DOI: {r['doi']}.", None))
    return _montar(seg)


def formatar_apa(r):
    def nome(a):
        ini = ' '.join(i + '.' for i in _iniciais(a['nome']))
        return f"{a['sobrenome']}, {ini}" if ini else a['sobrenome']

    nomes = [nome(a) for a in r['autores']]
    if len(nomes) > 20:
        autores = ', '.join(nomes[:19]) + ', . . . ' + nomes[-1]
    elif len(nomes) == 1:
        autores = nomes[0]
    elif len(nomes) == 2:
        autores = f'{nomes[0]}, & {nomes[1]}'
    elif nomes:
        autores = ', '.join(nomes[:-1]) + f', & {nomes[-1]}'
    else:
        autores = ''

    ano = f"({r['ano'] or 's.d.'})."
    seg = []
    if autores:
        seg.append((f"{_ponto(autores)} {ano} {_ponto(r['titulo'])} ", None))
    else:
        seg.append((f"{_ponto(r['titulo'])} {ano} ", None))

    if r['tipo'] == 'artigo' and r['fonte']:
        em = r['fonte'] + (f", {r['volume']}" if r['volume'] else '')
        seg.append((em, 'em'))
        resto = (f"({r['numero']})" if r['numero'] else '') + \
            (f", {r['paginas']}" if r['paginas'] else '') + '.'
        seg.append((resto, None))
    elif r['fonte']:
        seg.append((_ponto(r['fonte']), None))

    if r['doi']:
        seg.append((f" https://doi.org/{r['doi']}", None))
    return _montar(seg)


def formatar_vancouver(r, n):
    nomes = [f"{a['sobrenome']} {''.join(_iniciais(a['nome']))}".strip()
             for a in r['autores']]
    autores = ', '.join(nomes[:6]) + (', et al' if len(nomes) > 6 else '')

    seg = [(f'{n}. ', None)]
    if autores:
        seg.append((_ponto(autores) + ' ', None))
    seg.append((_ponto(r['titulo']) + ' ', None))

    if r['tipo'] == 'artigo' and r['fonte']:
        s = f"{r['fonte']}."
        if r['ano']:
            s += f" {r['ano']}"
            if r['volume'] or r['numero'] or r['paginas']:
                s += ';' + r['volume']
                if r['numero']:
                    s += f"({r['numero']})"
                if r['paginas']:
                    s += f":{_pag_vancouver(r['paginas'])}"
            s += '.'
        seg.append((s, None))
    else:
        resto = '; '.join(x for x in [r['fonte'], r['ano']] if x)
        seg.append((_ponto(resto) if resto else '', None))

    if r['doi']:
        seg.append((f" doi:{r['doi']}", None))
    return _montar(seg)


def _cita_numero(texto, n):
    for m in re.finditer(r'\[([\d,\s–\-]+)\]', texto):
        for token in re.split(r'\s*,\s*', m.group(1).strip()):
            faixa = re.split(r'\s*[–\-]\s*', token)
            try:
                if len(faixa) == 2 and int(faixa[0]) <= n <= int(faixa[1]):
                    return True
                if len(faixa) == 1 and int(faixa[0]) == n:
                    return True
            except ValueError:
                continue
    return False


def localizar_citacoes(corpo, r, indice):
    sob = r['autores'][0]['sobrenome'] if r['autores'] else ''
    padrao = None
    if len(sob) >= 3 and r['ano']:
        padrao = re.compile(
            re.escape(sob) + r'.{0,60}?' + re.escape(r['ano']), re.I | re.S)

    paginas = [num for num, texto in corpo
               if (padrao and padrao.search(texto)) or _cita_numero(texto, indice)]

    if not paginas:
        return 'Não localizada no corpo do texto'
    lista = ', '.join(str(p) for p in paginas[:6]) + \
        ('...' if len(paginas) > 6 else '')
    return f'Citada na(s) pág. {lista} (do PDF)'

@app.route('/api/citacoes', methods=['POST'])
def api_citacoes():
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    caminho = session.get('artigo_caminho')
    if not caminho or not os.path.exists(caminho):
        return {'erro': 'Nenhum artigo encontrado. Faça o upload novamente.'}, 400

    chave = f"{caminho}:{os.path.getmtime(caminho)}"
    if session.get('citacoes_chave') == chave and session.get('citacoes_geradas'):
        return session['citacoes_geradas']

    try:
        corpo, texto_refs = separar_corpo_e_referencias(caminho)
    except Exception as e:
        return {'erro': f'Erro ao ler o PDF: {str(e)}'}, 500

    if not texto_refs or len(texto_refs.strip()) < 50:
        return {'erro': 'Não encontrei a seção de referências neste PDF.'}, 404

    texto_refs = re.sub(r'[ \t]+', ' ', texto_refs)
    texto_refs = re.sub(r'\n\s*\n+', '\n', texto_refs)
    cortou = len(texto_refs) > MAX_CHARS_REFERENCIAS
    texto_refs = texto_refs[:MAX_CHARS_REFERENCIAS]

    try:
        brutas = extrair_referencias_llm(texto_refs)
    except (json.JSONDecodeError, ValueError):
        return {'erro': 'A IA retornou um formato inesperado. Tente novamente.'}, 500
    except Exception as e:
        return {'erro': f'Erro ao gerar citações: {str(e)}'}, 500

    refs = []
    for idx, b in enumerate(brutas, start=1):
        if isinstance(b, dict):
            r = _normalizar_ref(b)
            if r['titulo']:
                refs.append((idx, r))

    if not refs:
        return {'erro': 'Não consegui identificar referências neste PDF.'}, 404

    citacoes_formatadas = {'abnt': [], 'apa': [], 'vancouver': []}
    for pos, (idx, r) in enumerate(refs, start=1):
        local = localizar_citacoes(corpo, r, idx)
        citacoes_formatadas['abnt'].append({**formatar_abnt(r), 'ref': local})
        citacoes_formatadas['apa'].append({**formatar_apa(r), 'ref': local})
        citacoes_formatadas['vancouver'].append(
            {**formatar_vancouver(r, pos), 'ref': local})

    aviso = ''
    if cortou or len(brutas) >= MAX_REFERENCIAS:
        aviso = f'Foram processadas as primeiras {MAX_REFERENCIAS} referências do artigo.'

    resposta = {'citacoes': citacoes_formatadas, 'aviso': aviso}
    session['citacoes_geradas'] = resposta
    session['citacoes_chave'] = chave
    return resposta

# ROTA E API FICHA TÉCNICA
@app.route('/fichaTecnica')
def fichaTecnica():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('fichaTecnica.html')


FICHA_CAMPOS = ['objetivo', 'metodologia', 'amostra',
                'resultados', 'limitacoes', 'conclusao']


def extrair_texto_pdf(caminho, inicio=8000, fim=4000):
    paginas = extrair_paginas_pdf(caminho)
    texto = ' '.join(paginas)
    texto = re.sub(r'\s+', ' ', texto).strip()

    marcas = [m.start() for m in re.finditer(
        r'\b(references|referências|referencias|bibliography)\b', texto, re.I)]
    marcas = [p for p in marcas if p > len(texto) * 0.5]
    if marcas:
        texto = texto[:marcas[-1]]

    if len(texto) <= inicio + fim:
        return texto
    return texto[:inicio] + ' [...] ' + texto[-fim:]

@app.route('/api/ficha-tecnica', methods=['POST'])
def api_ficha_tecnica():
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    caminho = session.get('artigo_caminho')
    if not caminho or not os.path.exists(caminho):
        return {'erro': 'Nenhum artigo encontrado. Faça o upload novamente.'}, 400

    chave = f"{caminho}:{os.path.getmtime(caminho)}"
    if session.get('ficha_chave') == chave and session.get('ficha_gerada'):
        return {'ficha': session['ficha_gerada']}

    try:
        texto = extrair_texto_pdf(caminho)
    except Exception as e:
        return {'erro': f'Erro ao ler o PDF: {str(e)}'}, 500

    if not texto.strip():
        return {'erro': 'Não foi possível extrair texto do PDF.'}, 400

    messages = [
        {
            'role': 'system',
            'content': (
                'Você é um assistente acadêmico especializado em revisão sistemática. '
                'Leia o artigo científico e preencha uma ficha técnica em português do Brasil. '
                'Responda APENAS com um objeto JSON válido, sem markdown e sem texto extra, '
                'com exatamente estas chaves: "objetivo", "metodologia", "amostra", '
                '"resultados", "limitacoes", "conclusao". '
                'Cada valor deve ser uma string com 2 a 4 frases objetivas. '
                'Use somente informações presentes no artigo, sem inventar dados ou números. '
                'Se alguma informação não estiver no texto, use "Não informado no artigo.". '
                '"amostra" refere-se aos participantes, estudos ou base de dados analisados.'
            )
        },
        {
            'role': 'user',
            'content': f'Gere a ficha técnica do seguinte artigo:\n\n{texto}'
        }
    ]

    try:
        bruto = chamar_llm(messages, max_tokens=2500, temperature=0.2)
        achado = re.search(r'\{.*\}', bruto, re.S)
        if not achado:
            raise ValueError('formato inesperado')
        dados = json.loads(achado.group(0))

        ficha = {}
        for campo in FICHA_CAMPOS:
            valor = dados.get(campo, '')
            if isinstance(valor, list):
                valor = ' '.join(str(v) for v in valor)
            valor = str(valor).strip()
            ficha[campo] = valor or 'Não informado no artigo.'

        session['ficha_gerada'] = ficha
        session['ficha_chave'] = chave
        return {'ficha': ficha}

    except (json.JSONDecodeError, ValueError):
        return {'erro': 'A IA retornou um formato inesperado. Tente novamente.'}, 500
    except Exception as e:
        return {'erro': f'Erro ao gerar ficha técnica: {str(e)}'}, 500

# ROTA E API PLANO DE PESQUISA
@app.route('/planoPesquisa')
def planoPesquisa():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('planoPesquisa.html')

def _lista_texto(v, limite=20, tamanho=120):
    if not isinstance(v, list):
        return []
    itens = [str(x).strip()[:tamanho] for x in v if x is not None and str(x).strip()]
    return itens[:limite]


def gerar_plano_ia(pergunta, inclusao, exclusao, bancos):
    messages = [
        {
            'role': 'system',
            'content': (
                'Você é especialista em metodologia de revisão sistemática (PRISMA, PICO). '
                'A partir da pergunta de pesquisa e dos critérios do usuário, gere elementos '
                'do protocolo. Responda APENAS com um objeto JSON válido, sem markdown, com '
                'exatamente estas chaves: '
                '"pergunta_refinada" (uma única pergunta clara, em português, fiel ao tema do usuário); '
                '"pico" (objeto com "populacao", "intervencao", "comparacao" e "desfecho"; '
                'use "Não se aplica" quando o elemento não fizer sentido para o tema); '
                '"palavras_chave" (objeto com as listas "portugues" e "ingles", de 5 a 10 termos '
                'cada, incluindo sinônimos relevantes); '
                '"strings_busca" (lista de objetos {"banco": "", "string": ""}, exatamente um '
                'para cada banco de dados informado, na mesma ordem). '
                'As strings de busca devem usar operadores booleanos AND e OR, aspas para '
                'expressões, parênteses para agrupar sinônimos, e ser escritas em inglês '
                '(no SciELO, podem combinar português, inglês e espanhol). Adapte a sintaxe '
                'a cada base: PubMed com [Title/Abstract] e, quando couber, [MeSH Terms]; '
                'IEEE Xplore com "All Metadata":termo; Biblioteca Cochrane com :ti,ab,kw; '
                'Google Acadêmico sem códigos de campo e curta. '
                'Regras de construção: separe os conceitos da pergunta em blocos (por exemplo: '
                'técnica, contexto e tarefa); dentro de cada bloco una os sinônimos com OR e '
                'entre os blocos use AND. Quando a pergunta citar várias tarefas ou etapas '
                '(como triagem, extração e resumo), una-as com OR dentro do mesmo bloco, nunca '
                'com AND. Não inclua termos de desfecho ou desempenho (como accuracy, precision, '
                'recall, performance), pois restringem demais a busca. No PubMed, use [MeSH Terms] '
                'apenas para descritores MeSH reais (por exemplo, "Natural Language Processing"[MeSH Terms]) '
                'e [Title/Abstract] para as demais expressões. Na Biblioteca Cochrane e no SciELO, '
                'escreva apenas termos com AND, OR e aspas, sem códigos de campo. '
                'Não invente estudos, autores ou resultados.'
            )
        },
        {
            'role': 'user',
            'content': (
                f'Pergunta de pesquisa: {pergunta}\n'
                f'Critérios de inclusão: {"; ".join(inclusao) or "não informados"}\n'
                f'Critérios de exclusão: {"; ".join(exclusao) or "não informados"}\n'
                f'Bancos de dados: {"; ".join(bancos) or "nenhum"}'
            )
        }
    ]

    bruto = chamar_llm(messages, max_tokens=3000, temperature=0.3)
    achado = re.search(r'\{.*\}', bruto, re.S)
    if not achado:
        raise ValueError('formato inesperado')
    dados = json.loads(achado.group(0))
    if not isinstance(dados, dict):
        raise ValueError('formato inesperado')

    pico = dados.get('pico') if isinstance(dados.get('pico'), dict) else {}
    kw = dados.get('palavras_chave') if isinstance(dados.get('palavras_chave'), dict) else {}

    strings = []
    if isinstance(dados.get('strings_busca'), list):
        for item in dados['strings_busca']:
            if isinstance(item, dict):
                banco, texto = _txt(item.get('banco')), _txt(item.get('string'))
                if banco and texto:
                    strings.append({'banco': banco[:80], 'string': texto[:1500]})

    return {
        'pergunta_refinada': _txt(dados.get('pergunta_refinada')) or pergunta,
        'pico': {
            'populacao': _txt(pico.get('populacao')) or 'Não informado',
            'intervencao': _txt(pico.get('intervencao')) or 'Não informado',
            'comparacao': _txt(pico.get('comparacao')) or 'Não informado',
            'desfecho': _txt(pico.get('desfecho')) or 'Não informado',
        },
        'palavras_chave': {
            'portugues': _lista_texto(kw.get('portugues'), 12, 80),
            'ingles': _lista_texto(kw.get('ingles'), 12, 80),
        },
        'strings_busca': strings[:8],
    }

@app.route('/api/plano-pesquisa', methods=['POST'])
def api_plano_pesquisa():
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    data = request.get_json(silent=True) or {}
    pergunta = str(data.get('pergunta', '')).strip()
    if len(pergunta) < 10:
        return {'erro': 'Descreva sua pergunta de pesquisa (mínimo de 10 caracteres).'}, 400
    if len(pergunta) > 1500:
        return {'erro': 'Pergunta muito longa. Máximo de 1500 caracteres.'}, 400

    inclusao = _lista_texto(data.get('inclusao'))
    exclusao = _lista_texto(data.get('exclusao'))
    bancos = _lista_texto(data.get('bancos'), limite=8)

    try:
        return {'plano': gerar_plano_ia(pergunta, inclusao, exclusao, bancos)}
    except (json.JSONDecodeError, ValueError):
        return {'erro': 'A IA retornou um formato inesperado. Tente novamente.'}, 500
    except Exception as e:
        return {'erro': f'Erro ao gerar o plano: {str(e)}'}, 500

# ROTA E API TRADUTOR
@app.route('/traducao')
def traducao():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('traducao.html')


@app.route('/api/traduzir', methods=['POST'])
def api_traduzir():
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    data = request.get_json()
    texto = data.get('texto', '').strip()
    if not texto:
        return {'erro': 'Nenhum texto enviado.'}, 400
    if len(texto) > 3000:
        return {'erro': 'Texto muito longo. Máximo 3000 caracteres.'}, 400

    messages = [
        {"role": "system", "content": "Você é um tradutor técnico acadêmico. Traduza o texto para português"
         "claro e acessível, mantendo a precisão científica. Retorne APENAS a tradução."},
        {"role": "user", "content": texto}
    ]

    try:
        traducao_texto = chamar_llm(messages, max_tokens=1500, temperature=0.3)
        return {'traducao': traducao_texto}
    except Exception as e:
        return {'erro': f'Erro ao traduzir: {str(e)}'}, 500

# ROTA PARA ATUALIZAR O STATUS DO ARTIGO
@app.route('/atualizar-status/<projeto_id>/<int:artigo_idx>', methods=['POST'])
def atualizar_status(projeto_id, artigo_idx):
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401

    data = request.get_json()
    novo_status = data.get('status')

    if novo_status not in ['incluido', 'excluido', 'pendente']:
        return {'erro': 'Status inválido'}, 400

    p = Projeto.query.get(projeto_id)
    if not p or p.usuario_id != session['usuario_id'] or artigo_idx >= len(p.artigos):
        return {'erro': 'Artigo não encontrado'}, 404

    artigo = p.artigos[artigo_idx]
    artigo.status = novo_status
    db.session.commit()

    return {'ok': True}


if __name__ == '__main__':
    app.run(debug=True)