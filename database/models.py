# database/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Créer l'instance db ICI, pas dans app.py
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Modèle utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    region = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Word(db.Model):
    """Modèle mot"""
    __tablename__ = 'words'
    
    id = db.Column(db.Integer, primary_key=True)
    word_arabic = db.Column(db.String(100), nullable=False)
    word_latin = db.Column(db.String(100))
    definition = db.Column(db.Text, nullable=False)
    region = db.Column(db.String(50), default='توات')
    category = db.Column(db.String(50))
    example = db.Column(db.Text)
    arabic_letter = db.Column(db.String(20))
    status = db.Column(db.String(20), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    image_path = db.Column(db.String(255), nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Word {self.word_arabic}>'

class Submission(db.Model):
    """Modèle soumission"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    word_arabic = db.Column(db.String(100))
    definition = db.Column(db.Text)
    region = db.Column(db.String(50))
    example = db.Column(db.Text) 
    category = db.Column(db.String(50))
    submitted_by = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Submission {self.word_arabic}>'