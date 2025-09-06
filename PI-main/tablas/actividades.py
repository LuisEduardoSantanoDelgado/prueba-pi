from datetime import datetime
from db import db

class Actividades(db.Model):
    __tablename__ = 'actividades'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)

    prioridad = db.Column(db.String(20), nullable=False, default="Media")
    repetir = db.Column(db.String(20), nullable=False, default="Ninguna")
    imagen = db.Column(db.String(300), nullable=True)

    estado = db.Column(db.Boolean, nullable=False, default=True)
    completada = db.Column(db.Boolean, nullable=False, default=False)

    creada_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completada_en = db.Column(db.DateTime, nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("Usuarios", backref="actividades", lazy=True)