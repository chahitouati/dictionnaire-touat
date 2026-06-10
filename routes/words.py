# routes/words.py
from flask import Blueprint, render_template, request, jsonify
from app import db
from database.models import Word

words_bp = Blueprint('words', __name__)

@words_bp.route('/api/words')
def get_words():
    """API pour récupérer tous les mots"""
    words = Word.query.all()
    return jsonify([{
        'id': w.id,
        'word_arabic': w.word_arabic,
        'definition': w.definition,
        'region': w.region
    } for w in words])

@words_bp.route('/api/search')
def search():
    """Recherche de mots"""
    query = request.args.get('q', '')
    if query:
        results = Word.query.filter(
            Word.word_arabic.contains(query) | 
            Word.definition.contains(query)
        ).all()
    else:
        results = []
    
    return jsonify([{
        'id': w.id,
        'word_arabic': w.word_arabic,
        'definition': w.definition,
        'region': w.region
    } for w in results])

@words_bp.route('/by-letter/<letter>')
def by_letter(letter):
    """Mots par lettre arabe"""
    words = Word.query.filter_by(arabic_letter=letter).all()
    return render_template('words_by_letter.html', 
                          letter=letter, 
                          words=words)