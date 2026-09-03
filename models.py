from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(180), unique=True, nullable=False)
    senha         = db.Column(db.String(255), nullable=False)
    bio           = db.Column(db.Text, nullable=True)
    foto          = db.Column(db.String(255), nullable=True)  # caminho da foto no servidor
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Usuario {self.email}>'
    
class Projeto(db.Model):
    __tablename__ = 'projetos'

    id               = db.Column(db.Integer, primary_key=True)
    nome             = db.Column(db.String(200), nullable=False)
    data_criacao     = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id       = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    artigos = db.relationship('Artigo', backref='projeto', lazy=True, cascade='all, delete-orphan')

    @property
    def total(self):    return len(self.artigos)
    @property
    def incluido(self): return sum(1 for a in self.artigos if a.status == 'incluido')
    @property
    def excluido(self): return sum(1 for a in self.artigos if a.status == 'excluido')
    @property
    def pendente(self): return sum(1 for a in self.artigos if a.status == 'pendente')


class Artigo(db.Model):
    __tablename__ = 'artigos'

    id           = db.Column(db.Integer, primary_key=True)
    nome         = db.Column(db.String(255), nullable=False)
    caminho      = db.Column(db.String(500), nullable=True)
    status       = db.Column(db.Enum('pendente', 'incluido', 'excluido', name='status_artigo'), default='pendente')
    data_upload  = db.Column(db.DateTime, default=datetime.utcnow)
    projeto_id   = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)