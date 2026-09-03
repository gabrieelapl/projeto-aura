# AURA – Sistema de Revisão Sistemática Orientado por PLN

> Plataforma web desenvolvida por alunos da FATEC Registro que utiliza Inteligência Artificial e Processamento de Linguagem Natural (PLN) para auxiliar estudantes na compreensão de artigos científicos e na realização de Revisões Sistemáticas da Literatura (RSL).

---

## Sobre o Projeto

O AURA é uma plataforma web que visa democratizar o acesso a ferramentas de análise científica, facilitando o processo de revisão sistemática para estudantes universitários. A plataforma permite o upload de artigos científicos em PDF e oferece diversas funcionalidades baseadas em IA para auxiliar na leitura, compreensão e organização dos artigos.

---

## Tecnologias Utilizadas

**Back-end**
- Python 3.10+
- Flask — framework web
- Flask-Migrate — migrações de banco de dados
- Flask-SQLAlchemy — ORM para PostgreSQL
- PyMuPDF — extração de texto de PDFs
- python-dotenv — gerenciamento de variáveis de ambiente
- Werkzeug — utilitários Flask (upload seguro de arquivos)

**Front-end**
- HTML5 e CSS3 
- JavaScript 

**Banco de Dados**
- PostgreSQL

**APIs Externas**
- HuggingFace Inference API — geração de resumos, tradutor técnico, citações, ficha técnica e plano de pesquisa
- ElevenLabs API — síntese de voz (Text-to-Speech) para o resumo em áudio

---


## Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/gabrieelapl/projeto-aura.git
cd projeto-aura
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

Caso o arquivo `requirements.txt` não esteja atualizado, instale manualmente:

```bash
pip install flask flask-sqlalchemy flask-migrate python-dotenv pymupdf requests huggingface_hub psycopg2-binary werkzeug
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/aura_db
SECRET_KEY=aura_secret_key
HUGGINGFACE_API_KEY=hf_SuaChaveAqui
ELEVENLABS_API_KEY=SuaChaveElevenLabsAqui
FLASK_DEBUG=True
```

### 5. Crie o banco de dados

Abra o pgAdmin ou o terminal do PostgreSQL e execute:

```sql
CREATE DATABASE aura_db;
```

### 6. Execute as migrações

```bash
flask db init
flask db migrate -m "tabela usuarios"
flask db upgrade
```

### 7. Execute o projeto

```bash
python app.py
```

Acesse no navegador: **http://localhost:5000**
