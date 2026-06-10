# database/init_db.py
from app import app, db
from database.models import User, Word, Submission
import os

def init_db():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données...")
    
    # Supprimer la base de données existante si elle existe
    db_path = 'instance/dictionary.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Ancienne base de données supprimée")
    
    # Créer toutes les tables
    with app.app_context():
        db.create_all()
        print("✅ Tables créées avec succès")
        
        # Créer un utilisateur admin par défaut
        from werkzeug.security import generate_password_hash
        
        admin_user = User(
            username="admin",
            email="admin@touat.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            region="توات"
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print("👑 Utilisateur admin créé:")
        print("   Username: admin")
        print("   Email: admin@touat.com")
        print("   Password: admin123")
        
        # Ajouter quelques mots de test
        test_words = [
            Word(
                word_arabic="ابرة",
                definition="أداة الخياطة",
                region="توات",
                arabic_letter="حرف الالف",
                status="approved"
            ),
            Word(
                word_arabic="احنا",
                definition="بدلا من الضمير نحن",
                region="توات",
                arabic_letter="حرف الالف",
                status="approved"
            )
        ]
        
        for word in test_words:
            db.session.add(word)
        
        db.session.commit()
        print(f"📚 {len(test_words)} mots de test ajoutés")
        print("🎉 Base de données initialisée avec succès!")

if __name__ == "__main__":
    init_db()