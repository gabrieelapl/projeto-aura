# AURA – Sistema de Revisão Sistemática Orientado por PLN

> Plataforma web desenvolvida por alunos da FATEC Registro que utiliza Inteligência Artificial e Processamento de Linguagem Natural (PLN) para auxiliar estudantes na compreensão de artigos científicos e na realização de Revisões Sistemáticas da Literatura (RSL).

---

## Sobre o Projeto

O AURA é uma plataforma web que visa democratizar o acesso a ferramentas de análise científica, facilitando o processo de revisão sistemática para estudantes universitários. A plataforma permite o upload de artigos científicos em PDF e oferece funcionalidades baseadas em IA para auxiliar na leitura, compreensão e organização dos artigos.

---

## Tecnologias Utilizadas

**Back-end**
- Python 3.13
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Session, Flask-Bcrypt
- PyMuPDF e pypdf — extração de texto de PDFs
- Gunicorn — servidor de produção (no container)

**Front-end**
- Templates Jinja2, HTML5, CSS3 e JavaScript, servidos pelo próprio Flask

**Banco de Dados**
- PostgreSQL

**APIs Externas**
- Groq (via `huggingface_hub`) — modelo de linguagem para resumo, tradução, citações, ficha técnica e plano de pesquisa
- ElevenLabs — síntese de voz (Text-to-Speech)

**Infraestrutura e qualidade**
- Docker e Docker Compose
- pytest — testes automatizados
- ruff — lint
- GitHub Actions — integração contínua

---

## Executando com Docker (recomendado)

Pré-requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto.

### 1. Clone o repositório

```bash
git clone https://github.com/gabrieelapl/projeto-aura.git
cd projeto-aura
```

### 2. Configure as variáveis de ambiente

Copie o modelo e preencha com suas chaves:

```bash
cp .env.example .env
```

(No PowerShell: `Copy-Item .env.example .env`)

```env
POSTGRES_PASSWORD=sua_senha_do_banco
SECRET_KEY=uma_chave_secreta
GROQ_API_KEY=sua_chave_groq
ELEVENLABS_API_KEY=sua_chave_elevenlabs
```

### 3. Suba os containers

```bash
docker compose up --build
```

O Compose sobe dois serviços:

| Serviço | Descrição |
|---------|-----------|
| `db`    | PostgreSQL 16, com volume `pgdata` |
| `web`   | Aplicação Flask com Gunicorn; aplica as migrations (`flask db upgrade`) ao iniciar |

Os volumes `uploads`, `fotos` e `sessions` mantêm PDFs, áudios, fotos de perfil e sessões entre reinicializações.

### 4. Acesse

**http://localhost:8000**

Para parar, use `Ctrl+C` e `docker compose down`. Para apagar também o banco e os arquivos enviados, use `docker compose down -v`.

---

## Executando sem Docker (desenvolvimento local)

### 1. Ambiente virtual e dependências

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. Variáveis de ambiente

Crie um `.env` na raiz:

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/aura_db
SECRET_KEY=uma_chave_secreta
GROQ_API_KEY=sua_chave_groq
ELEVENLABS_API_KEY=sua_chave_elevenlabs
```

### 3. Banco de dados

Crie o banco no pgAdmin ou no terminal do PostgreSQL:

```sql
CREATE DATABASE aura_db;
```

O repositório já contém as migrations, então basta aplicá-las:

```bash
flask db upgrade
```

### 4. Execute

```bash
python app.py
```

Acesse **http://localhost:5000**

---

## Testes e lint

```bash
pip install -r requirements-dev.txt
python -m pytest -v
ruff check .
```

## Integração contínua

A cada push ou pull request na `main`, o GitHub Actions executa (`.github/workflows/ci.yml`):

1. **lint:** `ruff check .`
2. **test:** `pytest`
3. **docker-build:** `docker build`, executado apenas se lint e testes passarem
