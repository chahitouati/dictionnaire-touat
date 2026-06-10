# routes/submissions.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db

submissions_bp = Blueprint('submissions', __name__)

@submissions_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_word():
    if request.method == 'POST':
        # Pour l'instant, juste un message de succès
        flash('Fonctionnalité de soumission à venir!', 'info')
        return redirect(url_for('index'))
    
    return "Page de soumission - En développement"