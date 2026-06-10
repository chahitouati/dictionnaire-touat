# check_data.py
from app import app, db
from database.models import Word

with app.app_context():
    print("="*60)
    print("🔍 التحقق من البيانات")
    print("="*60)
    
    # البحث عن كلمة ابرة
    word = Word.query.filter_by(word_arabic="ابرة").first()
    if word:
        print(f"\n✅ كلمة 'ابرة':")
        print(f"   ID: {word.id}")
        print(f"   الحرف: {word.arabic_letter}")
        print(f"   التعريف: {word.definition}")
    else:
        print("\n❌ كلمة 'ابرة' غير موجودة")
    
    # عرض الكلمات التي تبدأ بحرف الألف
    print(f"\n📚 الكلمات التي تبدأ بحرف 'أ':")
    words_alif = Word.query.filter(Word.arabic_letter == 'أ').limit(10).all()
    for w in words_alif:
        print(f"   - {w.word_arabic}: {w.definition[:40]}...")
    
    # إحصائية الحروف
    print(f"\n📊 إحصائية الحروف:")
    from sqlalchemy import func
    letter_stats = db.session.query(Word.arabic_letter, func.count(Word.id)).group_by(Word.arabic_letter).all()
    for letter, count in sorted(letter_stats):
        print(f"   {letter}: {count} كلمة")
        