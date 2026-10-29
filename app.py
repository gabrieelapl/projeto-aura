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

        usuario.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
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
    
    artigos_list = [{'nome': a.nome, 'status': a.status, 'data': a.data, 'caminho': a.caminho} for a in p.artigos]
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
                           artigo_nome=session.get('artigo_nome', 'Artigo científico'),
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

    api_key = os.getenv('HUGGINGFACE_API_KEY')
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
        client = InferenceClient(api_key=api_key, provider='groq')
        result = client.chat_completion(
            messages=messages,
            model='meta-llama/Llama-3.3-70B-Instruct',
            max_tokens=1000,
            temperature=0.3
        )

        resumo_texto = result.choices[0].message.content.strip()
        session['resumo_gerado'] = resumo_texto
        return {'resumo': resumo_texto}
    except Exception as e:
        return {'erro': f'Erro ao gerar resumo: {str(e)}'}, 500

# ROTA E API DE ÁUDIO
@app.route('/audio')
def audio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('audio.html')

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
            return {'erro': f'Erro da API: {resp.status_code}'}, 500

        nome_audio = f"audio_{session['usuario_id']}.mp3"
        caminho = os.path.join(AUDIO_FOLDER, nome_audio)
        with open(caminho, 'wb') as f:
            f.write(resp.content)

        return {'audio_url': f'/static/uploads/audio/{nome_audio}'}
    except Exception as e:
        return {'erro': f'Erro ao gerar áudio: {str(e)}'}, 500

# ROTAS A SEREM FEITAS
@app.route('/citacoes')
def citacoes():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('citacoes.html')

@app.route('/fichaTecnica')
def fichaTecnica():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('fichaTecnica.html')

@app.route('/planoPesquisa')
def planoPesquisa():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('planoPesquisa.html')

# ROTA E API DO TRADUTOR TÉCNICO
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

    api_key = os.getenv('HUGGINGFACE_API_KEY')
    messages = [
        {"role": "system", "content": "Você é um tradutor técnico acadêmico. Traduza o texto para português claro e acessível, mantendo a precisão científica. Retorne APENAS a tradução."},
        {"role": "user", "content": texto}
    ]

    try:
        client = InferenceClient(api_key=api_key, provider='groq')
        result = client.chat_completion(
            messages=messages,
            model='meta-llama/Llama-3.3-70B-Instruct',
            max_tokens=800,
            temperature=0.3
        )
        return {'traducao': result.choices[0].message.content.strip()}
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