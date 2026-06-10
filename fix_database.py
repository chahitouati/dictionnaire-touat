# fix_database.py
import pandas as pd
from app import app, db
from database.models import Word

def fix_database():
    print("="*60)
    print("🔧 إصلاح قاعدة البيانات بالكامل")
    print("="*60)
    
    with app.app_context():
        # حذف جميع الكلمات القديمة
        old_count = Word.query.count()
        Word.query.delete()
        db.session.commit()
        print(f"🗑️ تم حذف {old_count} كلمة قديمة")
        
        # قراءة البيانات من Excel
        df = pd.read_excel('bdd.xlsx', sheet_name='Feuil2')
        print(f"📄 قراءة {len(df)} صف من Excel")
        
        # تنظيف وإضافة الكلمات
        added = 0
        errors = 0
        
        for index, row in df.iterrows():
            try:
                # قراءة البيانات
                mot = row.iloc[1]  # العمود B
                definition = row.iloc[2]  # العمود C
                region = row.iloc[3] if pd.notna(row.iloc[3]) else "توات"  # العمود D
                
                # تخطي الصفوف الفارغة
                if pd.isna(mot) or pd.isna(definition):
                    continue
                
                mot = str(mot).strip()
                definition = str(definition).strip()
                
                if mot == "" or definition == "":
                    continue
                
                # تحديد الحرف الأول بشكل صحيح
                premiere_lettre = mot[0]
                
                # إضافة الكلمة
                word = Word(
                    word_arabic=mot,
                    definition=definition,
                    region=region,
                    arabic_letter=premiere_lettre,
                    status='approved'
                )
                db.session.add(word)
                added += 1
                
                if added % 50 == 0:
                    print(f"   ✅ تمت إضافة {added} كلمة...")
                    
            except Exception as e:
                errors += 1
                print(f"⚠️ خطأ في السطر {index}: {e}")
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("📊 نتائج الإصلاح:")
        print(f"   ✅ تمت إضافة: {added} كلمة")
        print(f"   ❌ أخطاء: {errors}")
        print(f"   📚 إجمالي الكلمات: {Word.query.count()}")
        print("="*60)
        
        # التحقق من كلمة ابرة
        check_word = Word.query.filter_by(word_arabic="ابرة").first()
        if check_word:
            print("\n✅ كلمة 'ابرة' موجودة في قاعدة البيانات")
            print(f"   الحرف: {check_word.arabic_letter}")
            print(f"   التعريف: {check_word.definition}")
        else:
            print("\n❌ كلمة 'ابرة' غير موجودة في قاعدة البيانات")
        
        # عرض إحصائيات الحروف
        print("\n📊 إحصائيات الحروف:")
        letters = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
        for letter in letters:
            count = Word.query.filter_by(arabic_letter=letter).count()
            if count > 0:
                print(f"   {letter}: {count} كلمة")

if __name__ == '__main__':
    fix_database()