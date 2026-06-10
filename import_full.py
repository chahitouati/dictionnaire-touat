# import_full.py
import pandas as pd
import sys
from app import app, db
from database.models import Word

def import_all_words():
    print("="*60)
    print("🔄 استيراد جميع الكلمات من Excel")
    print("="*60)
    
    with app.app_context():
        # قراءة البيانات
        df = pd.read_excel('bdd.xlsx', sheet_name='Feuil2')
        print(f"📄 عدد الصفوف في Excel: {len(df)}")
        
        # عرض أول 5 صفوف للتحقق
        print("\n📋 أول 5 كلمات في Excel:")
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            print(f"   {i+1}. {row.iloc[1]} -> {row.iloc[2][:50]}...")
        
        # حذف جميع الكلمات الموجودة
        old_count = Word.query.count()
        Word.query.delete()
        db.session.commit()
        print(f"\n🗑️ تم حذف {old_count} كلمة قديمة")
        
        # إضافة الكلمات الجديدة
        added = 0
        skipped = 0
        
        for index, row in df.iterrows():
            try:
                # قراءة البيانات
                mot = row.iloc[1]  # العمود B
                definition = row.iloc[2]  # العمود C
                region = row.iloc[3] if pd.notna(row.iloc[3]) else "توات"  # العمود D
                example = row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else None  # العمود E
                
                # التحقق من صحة البيانات
                if pd.isna(mot) or pd.isna(definition):
                    skipped += 1
                    continue
                
                mot = str(mot).strip()
                definition = str(definition).strip()
                region = str(region).strip()
                
                if mot == "" or definition == "":
                    skipped += 1
                    continue
                
                # تحديد الحرف الأول
                premiere_lettre = mot[0] if mot else 'أ'
                
                # إضافة الكلمة
                word = Word(
                    word_arabic=mot,
                    definition=definition,
                    example=example if example and not pd.isna(example) else None,
                    region=region,
                    arabic_letter=premiere_lettre,
                    status='approved'
                )
                db.session.add(word)
                added += 1
                
                # عرض التقدم
                if added % 50 == 0:
                    print(f"   ✅ تم إضافة {added} كلمة...")
                    
            except Exception as e:
                print(f"⚠️ خطأ في السطر {index}: {e}")
                skipped += 1
        
        # حفظ التغييرات
        db.session.commit()
        
        # عرض النتائج
        print("\n" + "="*60)
        print("📊 نتائج الاستيراد:")
        print(f"   ✅ تم إضافة: {added} كلمة")
        print(f"   ⚠️ تم تخطي: {skipped} صف")
        print(f"   📚 إجمالي الكلمات في قاعدة البيانات: {Word.query.count()}")
        print("="*60)
        
        # التأكد من وجود كلمة "ابرة"
        test_word = Word.query.filter_by(word_arabic="ابرة").first()
        if test_word:
            print("\n✅ تم العثور على كلمة 'ابرة'")
            print(f"   التعريف: {test_word.definition}")
        else:
            print("\n❌ لم يتم العثور على كلمة 'ابرة'")
            print("   يرجى التحقق من ملف Excel")
        
        return added

if __name__ == '__main__':
    import_all_words()