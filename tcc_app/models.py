from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'))
    quantidade = db.Column(db.Integer)
    data = db.Column(db.Date)
