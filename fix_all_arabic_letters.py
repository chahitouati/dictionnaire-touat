# fix_all_arabic_letters.py
from app import app, db
from database.models import Word

def fix_all_arabic_letters():
    print("="*60)
    print("🔧 تصحيح الحروف العربية لجميع الكلمات")
    print("="*60)
    
    # قائمة الحروف العربية الصحيحة
    arabic_letters = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
    
    with app.app_context():
        words = Word.query.all()
        print(f"📚 عدد الكلمات: {len(words)}")
        
        corrected = 0
        for word in words:
            if word.word_arabic and len(word.word_arabic) > 0:
                # الحرف الأول الصحيح
                correct_letter = word.word_arabic[0]
                
                # إذا كان الحرف المخزن مختلفاً أو ليس حرفاً عربياً
                if word.arabic_letter != correct_letter or word.arabic_letter not in arabic_letters:
                    print(f"   تصحيح: {word.word_arabic} -> '{word.arabic_letter}' → '{correct_letter}'")
                    word.arabic_letter = correct_letter
                    corrected += 1
        
        db.session.commit()
        print(f"\n✅ تم تصحيح {corrected} كلمة")
        
        # التحقق من كلمة ابرة
        word = Word.query.filter_by(word_arabic='ابرة').first()
        if word:
            print(f"\n📝 كلمة 'ابرة': الحرف = '{word.arabic_letter}'")
        
        # عرض إحصائيات الحروف
        print("\n📊 إحصائيات الحروف بعد التصحيح:")
        from sqlalchemy import func
        stats = db.session.query(Word.arabic_letter, func.count(Word.id)).group_by(Word.arabic_letter).order_by(Word.arabic_letter).all()
        for letter, count in stats:
            if letter in arabic_letters:
                print(f"   {letter}: {count} كلمة")
            else:
                print(f"   ⚠️ '{letter}': {count} كلمة (غير صحيح)")

if __name__ == '__main__':
    fix_all_arabic_letters()