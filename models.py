# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Modèle pour les participants
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    numeros = db.Column(db.PickleType)
    etoiles = db.Column(db.PickleType)
    gain = db.Column(db.Float, default=0.0)
    match_numeros = db.Column(db.Integer, default=0)
    match_etoiles = db.Column(db.Integer, default=0)
    numbers_proximity = db.Column(db.Integer, default=0)  # Proximité des numéros
    stars_proximity = db.Column(db.Integer, default=0)    # Proximité des étoiles

# Modèle pour le tirage
class Tirage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numeros = db.Column(db.PickleType)
    etoiles = db.Column(db.PickleType)

# Modèle pour les réglages
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    max_participants = db.Column(db.Integer, default=100)
    jackpot_amount = db.Column(db.Float, default=3000000)
    max_numeros = db.Column(db.Integer, default=49)
    max_etoiles = db.Column(db.Integer, default=9)
    selection_numeros = db.Column(db.Integer, default=5)
    selection_etoiles = db.Column(db.Integer, default=2)
    max_gagnants = db.Column(db.Integer, default=10)

def init_db():
    db.create_all()
