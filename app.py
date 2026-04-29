from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = 'aura_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

# usuário provisorio
USUARIOS = [
    {'nome': 'Admin', 'email': 'admin@email.com', 'senha': '1234'}
]

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome            = request.form.get('nome', '').strip()
        email           = request.form.get('email', '').strip()
        senha           = request.form.get('senha', '').strip()

        if not nome or not email or not senha:
            return render_template('cadastro.html', erro='Preencha todos os campos.')

        if len(senha) < 4:
            return render_template('cadastro.html', erro='A senha deve ter pelo menos 4 caracteres.')
        
        if any(u['email'] == email for u in USUARIOS):
            return render_template('cadastro.html', erro='Este e-mail já está cadastrado.')

        USUARIOS.append({'nome': nome, 'email': email, 'senha': senha})

        # Redireciona para login após cadastro
        return redirect(url_for('login'))

    return render_template('cadastro.html')

# Usuário provisório 
USUARIO = {
    'email': 'admin@email.com',
    'senha': '1234'
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not email or not senha:
            return render_template('login.html', erro='Preencha todos os campos.')

        if email == USUARIO['email'] and senha == USUARIO['senha']:
            session['usuario'] = email
            return redirect(url_for('index'))
        elif email != USUARIO['email']:
            return render_template('login.html', erro='Usuário não encontrado.')
        else:
            return render_template('login.html', erro='Senha incorreta.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

# rota do perfil do usuario
@app.route('/perfil')
def perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('perfil.html')
if __name__ == '__main__':
    app.run(debug=True)