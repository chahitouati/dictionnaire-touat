# database/import_quick.py - Version ultra simple
import sys
import os

# Ajouter le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app
    from database.models import db, Word
    print("✅ Modules chargés")
except ImportError as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

def import_test_data():
    """Importe des données de test"""
    print("\n" + "="*50)
    print("🔄 IMPORTATION DE DONNÉES DE TEST")
    print("="*50)
    
    with app.app_context():
        # Vérifier combien de mots existent déjà
        avant = Word.query.count()
        print(f"📊 Mots existants: {avant}")
        
        # Données de test (les mots de ton Excel)
        test_mots = [
            # حرف الالف
            ("ابرة", "أداة الخياطة", "توات", "أ"),
            ("أح", "أتألم", "توات", "أ"),
            ("أحنا", "بدلا من الضمير نحن", "توات", "أ"),
            ("أخ", "أتقزز", "توات", "أ"),
            ("أراح", "امتنع", "توات", "أ"),
            ("إزار", "ما تستعمله المرأة كالغطاء", "توات", "أ"),
            ("أس", "أسكت", "توات", "أ"),
            ("يستاهل", "يستحق", "توات", "ي"),
            ("استنى", "انتظر", "توات", "أ"),
            ("اطرش", "الذي لا يسمع", "توات", "أ"),
            
            # حرف الباء
            ("البائر", "هو الأمر الباقي والكاسد", "توات", "ب"),
            ("بان", "ظهر", "توات", "ب"),
            ("البدلة", "الثياب", "توات", "ب"),
            ("البراد", "إناء الشاي", "توات", "ب"),
            ("براني", "صفة للإنسان الغريب", "توات", "ب"),
            ("البردعة", "ما يوضع فوق الدابة", "توات", "ب"),
            ("برق", "الإنكار والتكذيب", "توات", "ب"),
            ("بروقا", "دهش فلم يبصر", "توات", "ب"),
            ("ابرك", "أقعد", "توات", "أ"),
            ("بركش", "فتل الطعام", "توات", "ب"),
            
            # حرف الجيم
            ("جايح", "الفساد وعدم الصلاح", "توات", "ج"),
            ("جبس", "يكون في البناء", "توات", "ج"),
            ("جحش", "ابن الحمار", "توات", "ج"),
            ("جدى", "يعيش على عطية غيره", "توات", "ج"),
            ("أجدع", "الشاب الصغير القوي النشيط", "توات", "أ"),
        ]
        
        ajoutes = 0
        existants = 0
        
        for mot, definition, region, lettre in test_mots:
            # Vérifier si existe déjà
            if Word.query.filter_by(word_arabic=mot).first():
                existants += 1
                continue
            
            # Créer nouveau mot
            word = Word(
                word_arabic=mot,
                definition=definition,
                region=region,
                arabic_letter=lettre,
                status='approved'
            )
            db.session.add(word)
            ajoutes += 1
        
        # Sauvegarder
        db.session.commit()
        
        # Résultats
        apres = Word.query.count()
        
        print(f"\n📈 RÉSULTATS:")
        print(f"   ✅ Mots ajoutés: {ajoutes}")
        print(f"   ⚠️ Mots déjà existants: {existants}")
        print(f"   🔢 Total avant: {avant}")
        print(f"   🔢 Total après: {apres}")
        
        # Afficher quelques mots
        print(f"\n📝 APERÇU ({min(5, apres)} mots):")
        mots = Word.query.limit(5).all()
        for i, w in enumerate(mots, 1):
            print(f"   {i}. {w.word_arabic}: {w.definition}")
        
        print("\n✅ IMPORTATION TERMINÉE!")
        return True

if __name__ == '__main__':
    import_test_data()