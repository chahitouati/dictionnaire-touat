# link_media.py
import os
from app import app, db
from database.models import Word

# مسارات المجلدات
IMAGES_FOLDER = 'static/uploads/images'
AUDIO_FOLDER = 'static/uploads/audio'

# الامتدادات المسموحة
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}

def link_media():
    print("="*60)
    print("🖼️ ربط الصور والملفات الصوتية بالكلمات")
    print("="*60)
    
    with app.app_context():
        # جلب جميع الكلمات
        words = Word.query.all()
        print(f"📚 عدد الكلمات: {len(words)}")
        
        # إنشاء قاموس بأسماء الملفات المتوفرة
        images_dict = {}
        audio_dict = {}
        
        # قراءة الصور الموجودة
        if os.path.exists(IMAGES_FOLDER):
            for filename in os.listdir(IMAGES_FOLDER):
                name, ext = os.path.splitext(filename)
                if ext.lower() in IMAGE_EXTENSIONS:
                    images_dict[name] = f'uploads/images/{filename}'
            print(f"🖼️ عدد الصور الموجودة: {len(images_dict)}")
        else:
            print(f"⚠️ مجلد الصور غير موجود: {IMAGES_FOLDER}")
        
        # قراءة الملفات الصوتية الموجودة
        if os.path.exists(AUDIO_FOLDER):
            for filename in os.listdir(AUDIO_FOLDER):
                name, ext = os.path.splitext(filename)
                if ext.lower() in AUDIO_EXTENSIONS:
                    audio_dict[name] = f'uploads/audio/{filename}'
            print(f"🎵 عدد الملفات الصوتية: {len(audio_dict)}")
        else:
            print(f"⚠️ مجلد الصوتيات غير موجود: {AUDIO_FOLDER}")
        
        # ربط الكلمات بالصور والصوتيات
        updated_images = 0
        updated_audio = 0
        
        for word in words:
            # البحث عن صورة بنفس اسم الكلمة
            if word.word_arabic in images_dict:
                if word.image_path != images_dict[word.word_arabic]:
                    word.image_path = images_dict[word.word_arabic]
                    updated_images += 1
                    print(f"   🖼️ {word.word_arabic} -> صورة مرفقة")
            
            # البحث عن ملف صوتي بنفس اسم الكلمة
            if word.word_arabic in audio_dict:
                if word.audio_path != audio_dict[word.word_arabic]:
                    word.audio_path = audio_dict[word.word_arabic]
                    updated_audio += 1
                    print(f"   🎵 {word.word_arabic} -> صوت مرفق")
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("📊 نتائج الربط:")
        print(f"   🖼️ تم ربط {updated_images} صورة")
        print(f"   🎵 تم ربط {updated_audio} ملف صوتي")
        print("="*60)

if __name__ == '__main__':
    link_media()