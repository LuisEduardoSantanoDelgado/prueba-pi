from db import db

class Racha(db.Model):
    __tablename__ = 'racha'
    
    id = db.Column(db.Integer, primary_key=True)