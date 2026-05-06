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