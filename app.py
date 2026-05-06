from flask import Flask, render_template, request, redirect, session, url_for
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db, Usuario
from werkzeug.utils import secure_filename
import os
from flask import send_file
import uuid
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Banco de dados
app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Pastas de uploads
UPLOAD_FOLDER  = os.path.join('static', 'img', 'fotos')
ARTIGOS_FOLDER = os.path.join('static', 'uploads', 'artigos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ARTIGOS_FOLDER, exist_ok=True)


#ROTAS

#substituir pelo bd dps
def get_projetos():
    return session.get('projetos', [])

def save_projetos(projetos):
    session['projetos'] = projetos
    session.modified = True

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', projetos=get_projetos())



@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not nome or not email or not senha:
            return render_template('cadastro.html', erro='Preencha todos os campos.')
        if len(senha) < 6:
            return render_template('cadastro.html', erro='A senha deve ter pelo menos 6 caracteres.')
        if Usuario.query.filter_by(email=email).first():
            return render_template('cadastro.html', erro='Este e-mail já está cadastrado.')

        novo = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(novo)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not email or not senha:
            return render_template('login.html', erro='Preencha todos os campos.')

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            return render_template('login.html', erro='Usuário não encontrado.')
        if usuario.senha != senha:
            return render_template('login.html', erro='Senha incorreta.')

        session['usuario_id'] = usuario.id
        session['usuario']    = usuario.email
        session['nome']       = usuario.nome
        session['bio']        = usuario.bio or ''
        session['foto']       = usuario.foto or ''

        meses = {
            'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
            'April': 'abril', 'May': 'maio', 'June': 'junho',
            'July': 'julho', 'August': 'agosto', 'September': 'setembro',
            'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
        }
        data = usuario.data_cadastro.strftime('%d de %B de %Y')
        for en, pt in meses.items():
            data = data.replace(en, pt)
        session['membro_desde'] = data

        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('perfil.html')


@app.route('/editarPerfil', methods=['GET', 'POST'])
def editarPerfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        bio  = request.form.get('bio', '').strip()

        if not nome:
            return render_template('editarPerfil.html', erro='O nome não pode estar vazio.')

        usuario.nome = nome
        usuario.bio  = bio
        session['nome'] = nome
        session['bio']  = bio

        foto = request.files.get('foto')
        if foto and foto.filename:
            nome_arquivo = f"{session['usuario_id']}_{secure_filename(foto.filename)}"
            foto.save(os.path.join(UPLOAD_FOLDER, nome_arquivo))
            usuario.foto    = nome_arquivo
            session['foto'] = nome_arquivo

        db.session.commit()
        return redirect(url_for('perfil'))

    return render_template('editarPerfil.html')


@app.route('/alterarSenha', methods=['GET', 'POST'])
def alterarSenha():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        senha_atual     = request.form.get('senha_atual', '').strip()
        nova_senha      = request.form.get('nova_senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()

        if usuario.senha != senha_atual:
            return render_template('alterarSenha.html', erro='Senha atual incorreta.')
        if nova_senha != confirmar_senha:
            return render_template('alterarSenha.html', erro='As senhas não coincidem.')
        if len(nova_senha) < 6:
            return render_template('alterarSenha.html', erro='A nova senha deve ter pelo menos 6 caracteres.')

        usuario.senha = nova_senha
        db.session.commit()
        return render_template('alterarSenha.html', sucesso='Senha alterada com sucesso!')

    return render_template('alterarSenha.html')


@app.route('/excluir-conta')
def excluirConta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    db.session.delete(usuario)
    db.session.commit()
    session.clear()
    return redirect(url_for('cadastro'))


@app.route('/upload', methods=['POST'])
def upload():

    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    artigo       = request.files.get('artigo')
    nome_artigo  = request.form.get('artigo_nome', 'Artigo')
    tamanho      = request.form.get('artigo_tamanho', '')
    projeto_tipo = request.form.get('projeto_tipo', 'novo')
    projeto_id   = request.form.get('projeto_id', '')
    nome_novo    = request.form.get('projeto_novo', '').strip()

    # Salva o arquivo
    if artigo and artigo.filename:
        nome_arquivo = secure_filename(artigo.filename)
        pasta = os.path.join(ARTIGOS_FOLDER, str(session['usuario_id']))
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_arquivo)
        artigo.save(caminho)
        session['artigo_nome']    = nome_artigo
        session['artigo_meta']    = f'{tamanho} · PDF'
        session['artigo_caminho'] = caminho

    projetos = get_projetos()

    if projeto_tipo == 'novo':
        # Lê o nome do campo de texto
        nome_projeto = request.form.get('input-novo-projeto', '').strip() or nome_artigo
        novo = {
            'id':       str(uuid.uuid4())[:8],
            'nome':     nome_projeto,
            'data':     datetime.now().strftime('%d de %B de %Y'),
            'total':    1,
            'incluido': 0,
            'excluido': 0,
            'pendente': 1,
            'artigos':  [{'nome': nome_artigo, 'status': 'pendente'}]
        }
        projetos.append(novo)
    else:
        # Adiciona ao projeto existente
        for p in projetos:
            if p['id'] == projeto_id:
                p['artigos'].append({'nome': nome_artigo, 'status': 'pendente'})
                p['total']    += 1
                p['pendente'] += 1
                break

    save_projetos(projetos)
    return redirect(url_for('funcionalidades'))


@app.route('/renomear-projeto/<id>', methods=['POST'])
def renomear_projeto(id):
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401
    data     = request.get_json()
    projetos = get_projetos()
    for p in projetos:
        if p['id'] == id:
            p['nome'] = data.get('nome', p['nome'])
            break
    save_projetos(projetos)
    return {'ok': True}


@app.route('/deletar-projeto/<id>', methods=['POST'])
def deletar_projeto(id):
    if 'usuario_id' not in session:
        return {'erro': 'Não autorizado'}, 401
    projetos = [p for p in get_projetos() if p['id'] != id]
    save_projetos(projetos)
    return {'ok': True}


@app.route('/projeto/<id>')
def projeto(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    projetos = get_projetos()
    p = next((x for x in projetos if x['id'] == id), None)
    if not p:
        return redirect(url_for('index'))
    return render_template('projeto.html', projeto=p)


@app.route('/funcionalidades')
def funcionalidades():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    return render_template('funcionalidades.html',
        artigo_nome=session.get('artigo_nome', 'Artigo científico'),
        artigo_meta=session.get('artigo_meta', 'Arquivo carregado')
    )

# função para ver o pdf na tel de funcionalidades
@app.route('/ver-pdf')
def ver_pdf():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    caminho = session.get('artigo_caminho')
    if not caminho or not os.path.exists(caminho):
        return 'Arquivo não encontrado', 404
    
    return send_file(caminho, mimetype='application/pdf')

#  ger\r resumo
@app.route('/resumo')
def resumo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('resumo.html')

# gerar audio
@app.route('/audio')
def audio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('audio.html')

# citações
@app.route('/citacoes')
def citacoes():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('citacoes.html')

# ficha tecnica
@app.route('/fichaTecnica')
def fichaTecnica():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('fichaTecnica.html')

# plano de pesquisa

@app.route('/planoPesquisa')
def planoPesquisa():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('planoPesquisa.html')

# tradução
@app.route('/traducao')
def traducao():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('traducao.html')



if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')