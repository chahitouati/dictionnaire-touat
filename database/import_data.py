# database/import_excel_complete.py
import sys
import os
import pandas as pd

# Ajouter le chemin parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database.models import db, Word

def import_from_excel():
    """Importe TOUTES les données de ton Excel"""
    print("="*70)
    print("📥 IMPORTATION COMPLÈTE DEPUIS EXCEL")
    print("="*70)
    
    # Nom de ton fichier Excel
    excel_file = "bdd.xlsx"
    
    # Vérifier si le fichier existe
    if not os.path.exists(excel_file):
        print(f"❌ Fichier non trouvé: {excel_file}")
        print("📁 Fichiers disponibles:")
        for f in os.listdir('.'):
            if f.endswith('.xlsx'):
                print(f"  - {f}")
        return False
    
    try:
        # Lire le fichier Excel
        print(f"📄 Lecture du fichier: {excel_file}")
        
        # Ton Excel a deux feuilles: Feuil1 (organisé par lettres) et Feuil2 (liste simple)
        # On va lire Feuil2 qui est plus simple
        try:
            df = pd.read_excel(excel_file, sheet_name='Feuil2')
            print("✅ Feuille 'Feuil2' chargée")
        except:
            # Essayer la première feuille
            df = pd.read_excel(excel_file, sheet_name=0)
            print("✅ Première feuille chargée")
        
        print(f"📊 Dimensions: {df.shape[0]} lignes x {df.shape[1]} colonnes")
        print(f"📋 Colonnes: {list(df.columns)}")
        
        # Afficher un aperçu
        print("\n🔍 Aperçu des premières lignes:")
        print(df.head().to_string())
        
        with app.app_context():
            # Compter avant
            avant = Word.query.count()
            print(f"\n📈 Avant import: {avant} mots")
            
            mots_ajoutes = 0
            mots_existants = 0
            erreurs = 0
            
            # Traiter chaque ligne
            for index, row in df.iterrows():
                try:
                    # Dans Feuil2, les colonnes sont:
                    # Colonne B: الكلمة (mot)
                    # Colonne C: تعريف (définition) 
                    # Colonne D: المنطقة (région)
                    # Colonne E: المجال (catégorie)
                    
                    # Récupérer les données
                    mot_arabe = None
                    definition = None
                    region = "توات"
                    categorie = None
                    
                    # Chercher les colonnes par index (plus sûr)
                    if len(df.columns) >= 2:
                        mot_arabe = row.iloc[1] if pd.notna(row.iloc[1]) else None  # Colonne B
                    if len(df.columns) >= 3:
                        definition = row.iloc[2] if pd.notna(row.iloc[2]) else None  # Colonne C
                    if len(df.columns) >= 4:
                        region_val = row.iloc[3] if pd.notna(row.iloc[3]) else None  # Colonne D
                        if region_val:
                            region = str(region_val).strip()
                    if len(df.columns) >= 5:
                        categorie_val = row.iloc[4] if pd.notna(row.iloc[4]) else None  # Colonne E
                        if categorie_val:
                            categorie = str(categorie_val).strip()
                    
                    # Vérifier les données obligatoires
                    if not mot_arabe or pd.isna(mot_arabe) or str(mot_arabe).strip() == '':
                        continue
                    
                    if not definition or pd.isna(definition):
                        definition = "غير محدد"
                    
                    # Nettoyer
                    mot_arabe = str(mot_arabe).strip()
                    definition = str(definition).strip()
                    
                    # Vérifier si le mot existe déjà
                    if Word.query.filter_by(word_arabic=mot_arabe).first():
                        mots_existants += 1
                        continue
                    
                    # Déterminer la première lettre arabe
                    if mot_arabe and len(mot_arabe) > 0:
                        premiere_lettre = mot_arabe[0]
                    else:
                        premiere_lettre = 'أ'
                    
                    # Créer le mot
                    nouveau_mot = Word(
                        word_arabic=mot_arabe,
                        definition=definition,
                        region=region,
                        category=categorie,
                        arabic_letter=premiere_lettre,
                        status='approved'
                    )
                    
                    db.session.add(nouveau_mot)
                    mots_ajoutes += 1
                    
                    # Afficher progression
                    if mots_ajoutes % 25 == 0:
                        print(f"  → {mots_ajoutes} mots traités...")
                        
                except Exception as e:
                    erreurs += 1
                    if erreurs <= 3:  # Afficher seulement quelques erreurs
                        print(f"  ⚠️ Erreur ligne {index}: {str(e)[:50]}...")
                    continue
            
            # Sauvegarder tout
            db.session.commit()
            
            # Compter après
            apres = Word.query.count()
            
            # Afficher le résumé
            print("\n" + "="*70)
            print("📊 RÉSUMÉ DE L'IMPORTATION")
            print("="*70)
            print(f"   📄 Fichier source: {excel_file}")
            print(f"   📈 Lignes dans Excel: {len(df)}")
            print(f"   ✅ Mots ajoutés: {mots_ajoutes}")
            print(f"   ⚠️ Mots déjà existants: {mots_existants}")
            print(f"   ❌ Erreurs: {erreurs}")
            print(f"   🔢 Total avant: {avant}")
            print(f"   🔢 Total après: {apres}")
            print(f"   📈 Augmentation: {apres - avant}")
            print("="*70)
            
            # Afficher des statistiques
            if apres > 0:
                print("\n📊 STATISTIQUES:")
                
                # Mots par lettre
                print("\n🔤 MOTS PAR LETTRE:")
                lettres = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
                for lettre in lettres:
                    count = Word.query.filter_by(arabic_letter=lettre).count()
                    if count > 0:
                        print(f"   {lettre}: {count:3d} mot(s)")
                
                # Mots par région
                print("\n🌍 MOTS PAR RÉGION:")
                regions_data = {}
                mots = Word.query.all()
                for mot in mots:
                    region = mot.region or "غير محدد"
                    if region not in regions_data:
                        regions_data[region] = 0
                    regions_data[region] += 1
                
                for region, count in regions_data.items():
                    print(f"   {region}: {count} mot(s)")
                
                # Afficher un échantillon
                print(f"\n📝 ÉCHANTILLON ({min(10, apres)} mots):")
                derniers_mots = Word.query.order_by(Word.id.desc()).limit(10).all()
                for i, mot in enumerate(derniers_mots, 1):
                    print(f"   {i:2d}. {mot.word_arabic}: {mot.definition[:40]}...")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = import_from_excel()
    if success:
        print("\n✅ IMPORTATION RÉUSSIE!")
        print("🚀 Redémarre Flask: python app.py")
    else:
        print("\n❌ IMPORTATION ÉCHOUÉE!")
        sys.exit(1)