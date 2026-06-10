# routes/admin.py - Ajoute ces fonctions
from flask import render_template
from datetime import datetime
from app import db
from database.models import User, Submission

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    pending_count = Submission.query.filter_by(status='pending').count()
    total_users = User.query.count()
    total_words = Word.query.count()  # Assure-toi d'avoir importé Word
    
    return render_template('admin/dashboard.html',
                          pending_count=pending_count,
                          total_users=total_users,
                          total_words=total_words,
                          current_date=datetime.now())

@admin_bp.route('/admin/submissions')
def admin_submissions():
    submissions = Submission.query.filter_by(status='pending').all()
    return render_template('admin/submissions.html', 
                          submissions=submissions)

@admin_bp.route('/admin/users')
def admin_users():
    users = User.query.all()
    total_users = len(users)
    active_users = User.query.count()  # À adapter avec une logique d'activité
    admins_count = User.query.filter_by(role='admin').count()
    
    return render_template('admin/users.html',
                          users=users,
                          total_users=total_users,
                          active_users=active_users,
                          admins_count=admins_count,
                          today_registrations=0,  # À adapter
                          current_date=datetime.now())