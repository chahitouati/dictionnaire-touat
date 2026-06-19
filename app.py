# app.py - Version complète avec toutes les routes
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import pandas
from datetime import datetime
import cloudinary
import cloudinary.uploader


# Configuration des uploads
UPLOAD_FOLDER_IMAGES = 'static/uploads/images'
UPLOAD_FOLDER_AUDIO = 'static/uploads/audio'
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_EXTENSIONS_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}

# Créer les dossiers s'ils n'existent pas
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_AUDIO, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder, allowed_extensions):
    if file and file.filename and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        filepath = os.path.join(folder, unique_name)
        file.save(filepath)
        return filepath.replace('static/', '')
    return None

# Créer l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dictionary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# Initialiser LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Importer db depuis models.py
from database.models import db
db.init_app(app)

# Importer les modèles APRÈS avoir initialisé db
from database.models import User, Word, Submission

# Configurer user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Créer les tables au démarrage
with app.app_context():
    db.create_all()
    # Créer le compte admin s'il n'existe pas
    if User.query.filter_by(email='admin@touat.com').first() is None:
        admin = User(
            username='admin',
            email='admin@touat.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            region='توات'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Compte admin créé avec succès !")
    else:
        print("✅ Compte admin existe déjà")
    # Vérifier si la base est vide
    if Word.query.count() == 0:
        print("📚 Base de données vide, importation des mots...")
        try:
            import pandas as pd
            df = pd.read_excel('bdd.xlsx', sheet_name='Feuil2')
            added = 0
            for _, row in df.iterrows():
                if pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
                    mot = str(row.iloc[1]).strip()
                    definition = str(row.iloc[2]).strip()
                    region = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else 'توات'
                    
                    word = Word(
                        word_arabic=mot,
                        definition=definition,
                        region=region,
                        arabic_letter=mot[0] if mot else 'أ',
                        status='approved'
                    )
                    db.session.add(word)
                    added += 1
            db.session.commit()
            print(f"✅ {added} mots importés avec succès !")
        except Exception as e:
            print(f"⚠️ Erreur d'importation : {e}")

# ===== PAGE D'ACCUEIL =====

@app.route('/')
def index():
    """Page d'accueil"""
    words = Word.query.order_by(Word.id.desc()).limit(12).all()
    total_words = Word.query.count()
    users_count = User.query.count()
    
    return render_template('index.html', 
                          words=words, 
                          total_words=total_words,
                          users_count=users_count)

# ===== RECHERCHE =====

@app.route('/search', methods=['GET'])
def search():
    """Page de recherche"""
    query = request.args.get('q', '').strip()
    
    if query:
        # Recherche dans les mots arabes et les définitions
        words = Word.query.filter(
            Word.word_arabic.contains(query) | 
            Word.definition.contains(query) |
            Word.word_latin.contains(query)
        ).all()
    else:
        words = []
    
    return render_template('search.html', 
                          query=query, 
                          results=words,
                          results_count=len(words))

@app.route('/admin/link-media')
@login_required
def link_media():
    """Lier les fichiers images/audio aux mots par nom"""
    if current_user.role != 'admin':
        return "Non autorisé", 403
    
    import os
    words = Word.query.all()
    linked_images = 0
    linked_audio = 0
    errors = []
    
    for word in words:
        # Vérifier si une image existe
        found_image = False
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            image_path = f"uploads/images/{word.word_arabic}{ext}"
            if os.path.exists(f"static/{image_path}"):
                word.image_path = image_path
                linked_images += 1
                found_image = True
                break
        
        # Vérifier si un audio existe
        found_audio = False
        for ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            audio_path = f"uploads/audio/{word.word_arabic}{ext}"
            if os.path.exists(f"static/{audio_path}"):
                word.audio_path = audio_path
                linked_audio += 1
                found_audio = True
                break
        
        if not found_image and not found_audio:
            errors.append(word.word_arabic)
    
    db.session.commit()
    
    result = f"""
    ✅ {linked_images} images liées<br>
    ✅ {linked_audio} audios liés<br>
    ⚠️ {len(errors)} mots sans média: {', '.join(errors[:10])}
    """
    return result

@app.route('/debug/media')
@login_required
def debug_media():
    words = Word.query.limit(10).all()
    result = []
    for w in words:
        result.append({
            'id': w.id,
            'word': w.word_arabic,
            'image_path': w.image_path,
            'audio_path': w.audio_path,
            'image_is_url': w.image_path.startswith('http') if w.image_path else False,
            'audio_is_url': w.audio_path.startswith('http') if w.audio_path else False
        })
    return jsonify(result)

# ===== NAVIGATION PAR LETTRES =====

@app.route('/by-letter/<letter>')
def by_letter(letter):
    """Mots par lettre arabe"""
    # Recherche les mots qui commencent par cette lettre
    words = Word.query.filter(Word.word_arabic.startswith(letter)).all()
    if not words:
        words = Word.query.filter_by(arabic_letter=letter).all()

    return render_template('by_letter.html',
                          letter=letter,
                          words=words,
                          words_count=len(words))

# ===== API =====

@app.route('/api/words')
def api_words():
    """API JSON de tous les mots"""
    try:
        words = Word.query.all()
        
        data = [{
            'id': w.id,
            'word_arabic': w.word_arabic,
            'definition': w.definition,
            'region': w.region,
            'category': w.category,
            'arabic_letter': w.arabic_letter,
            'created_at': w.created_at.isoformat() if w.created_at else None
        } for w in words]
        
        return jsonify({
            'success': True,
            'count': len(data),
            'words': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ET pour une page HTML simple qui affiche tous les mots :
@app.route('/all-words')
def all_words():
    """Page HTML simple avec tous les mots"""
    words = Word.query.all()
    
    html = """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>جميع الكلمات - معجم توات</title>
        <style>
            body { font-family: Arial; padding: 20px; direction: rtl; }
            .word { border-bottom: 1px solid #eee; padding: 10px 0; }
            .arabic { font-size: 1.2rem; font-weight: bold; color: #2c3e50; }
            .definition { color: #7f8c8d; }
            .count { background: #3498db; color: white; padding: 5px 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>جميع الكلمات في القاموس</h1>
        <p>عدد الكلمات: <span class="count">""" + str(len(words)) + """</span></p>
        <p><a href="/">← العودة للصفحة الرئيسية</a></p>
        <hr>
    """
    
    for word in words:
        html += f"""
        <div class="word">
            <div class="arabic">{word.word_arabic}</div>
            <div class="definition">{word.definition}</div>
            <small style="color: #95a5a6;">{word.region} | {word.arabic_letter}</small>
        </div>
        """
    
    html += """
        <hr>
        <p><a href="/">← العودة للصفحة الرئيسية</a></p>
    </body>
    </html>
    """
    
    return html

@app.route('/api/search')
def api_search():
    """API de recherche"""
    query = request.args.get('q', '')
    
    if query:
        words = Word.query.filter(
            Word.word_arabic.contains(query) | 
            Word.definition.contains(query)
        ).limit(20).all()
    else:
        words = []
    
    return jsonify([{
        'word_arabic': w.word_arabic,
        'definition': w.definition,
        'region': w.region
    } for w in words])

# ===== AUTHENTIFICATION =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('✅ تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('index'))
        else:
            flash('❌ البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('❌ كلمات المرور غير متطابقة', 'error')
        elif User.query.filter_by(email=email).first():
            flash('❌ هذا البريد الإلكتروني مستخدم بالفعل', 'error')
        elif User.query.filter_by(username=username).first():
            flash('❌ اسم المستخدم هذا مستخدم بالفعل', 'error')
        else:
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role='user',
                region='توات'
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('✅ تم إنشاء حسابك بنجاح! يمكنك تسجيل الدخول الآن', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('👋 تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))

# ===== ADMIN =====

# ===== ADMIN ROUTES =====

@app.route('/admin')
@login_required
def admin_dashboard():
    """لوحة تحكم المشرف"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح لك بالدخول', 'error')
        return redirect(url_for('index'))
    
    total_users = User.query.count()
    total_words = Word.query.count()
    pending_count = Submission.query.filter_by(status='pending').count()
    current_date = datetime.now()
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          total_words=total_words,
                          pending_count=pending_count,
                          current_date=current_date)

@app.route('/admin/submissions')
@login_required
def admin_submissions():
    """عرض جميع الطلبات المعلقة"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح لك بالدخول', 'error')
        return redirect(url_for('index'))
    
    submissions = Submission.query.filter_by(status='pending').all()
    return render_template('admin/submissions.html', submissions=submissions)

@app.route('/admin/approve/<int:submission_id>')
@login_required
def approve_submission(submission_id):
    """الموافقة على طلب وإضافته إلى القاموس مع الصورة والصوت"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    submission = Submission.query.get_or_404(submission_id)
    
    # تحويل الطلب إلى كلمة حقيقية (مع إمكانية إضافة صورة/صوت لاحقاً)
    new_word = Word(
        word_arabic=submission.word_arabic,
        definition=submission.definition,
        example=submission.example,
        region=submission.region,
        category=submission.category,
        arabic_letter=submission.word_arabic[0] if submission.word_arabic else 'أ',
        status='approved',
        image_path=submission.image_path,  # نقل مسار الصورة
        audio_path=submission.audio_path   # نقل مسار الصوت
        # يمكن إضافة image_path و audio_path هنا إذا كانت موجودة في Submission
    )
    db.session.add(new_word)
    
    # تحديث حالة الطلب
    submission.status = 'approved'
    db.session.commit()
    
    flash(f'✅ تمت الموافقة على "{submission.word_arabic}" وإضافته للقاموس', 'success')
    return redirect(url_for('admin_submissions'))

@app.route('/admin/reject/<int:submission_id>')
@login_required
def reject_submission(submission_id):
    """رفض الطلب"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    submission = Submission.query.get_or_404(submission_id)
    submission.status = 'rejected'
    db.session.commit()
    
    flash(f'❌ تم رفض "{submission.word_arabic}"', 'info')
    return redirect(url_for('admin_submissions'))

@app.route('/admin/users')
@login_required
def admin_users():
    """إدارة المستخدمين"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()
    total_users = len(users)
    active_users = len([u for u in users if True])  # جميعهم نشطون حالياً
    admins_count = len([u for u in users if u.role == 'admin'])
    today_registrations = len([u for u in users if u.created_at.date() == datetime.now().date()])
    current_date = datetime.now()  # ⬅️ أضف هذا السطر
    
    return render_template('admin/users.html', 
                          users=users,
                          total_users=total_users,
                          active_users=active_users,
                          admins_count=admins_count,
                          today_registrations=today_registrations,
                          current_date=current_date)  # ⬅️ أضف current_date هنا
# ===== SOUMISSION DE MOTS =====

# تكوين رفع الملفات (ضعها في بداية الملف بعد الاستيرادات)
UPLOAD_FOLDER_IMAGES = 'static/uploads/images'
UPLOAD_FOLDER_AUDIO = 'static/uploads/audio'
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_EXTENSIONS_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}

# إنشاء المجلدات إذا لم تكن موجودة
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_AUDIO, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions



@app.context_processor
def inject_background():
    return dict(background_image='/static/images/touat.jpg')

@app.route('/test-bg')
def test_bg():
    return render_template('test.html')

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_word():
    """إضافة كلمة جديدة - تمر عبر المراجعة"""
    if request.method == 'POST':
        try:
            word_arabic = request.form.get('word_arabic', '').strip()
            definition = request.form.get('definition', '').strip()
            region = request.form.get('region', 'توات').strip()
            example = request.form.get('example', '').strip()
            category = request.form.get('category', '').strip()

            if not word_arabic or not definition:
                flash('❌ الكلمة والتعريف مطلوبان', 'error')
                return redirect(url_for('submit_word'))

            # حفظ الصورة والصوت
            image_file = request.files.get('image')
            audio_file = request.files.get('audio')
            
            image_path = save_file(image_file, UPLOAD_FOLDER_IMAGES, ALLOWED_EXTENSIONS_IMAGES)
            audio_path = save_file(audio_file, UPLOAD_FOLDER_AUDIO, ALLOWED_EXTENSIONS_AUDIO)

            # التحقق من عدم وجود الكلمة مسبقاً
            existing = Word.query.filter_by(word_arabic=word_arabic).first()
            if existing:
                flash(f'⚠️ الكلمة "{word_arabic}" موجودة بالفعل', 'info')
                return redirect(url_for('word_detail', word_id=existing.id))

            # ✅ إنشاء طلب مراجعة (وليس كلمة مباشرة)
            submission = Submission(
                word_arabic=word_arabic,
                definition=definition,
                example=example if example else None,
                region=region,
                category=category if category else None,
                submitted_by=current_user.id,
                status='pending',
                image_path=image_path,  # حفظ مسار الصورة
                audio_path=audio_path   # حفظ مسار الصوت
                # ملاحظة: الصورة والصوت سيتم ربطهما عند الموافقة
                # أو يمكن إضافتهما إلى Submission أيضاً
            )

            db.session.add(submission)
            db.session.commit()

            flash(f'✅ تم إرسال "{word_arabic}" للمراجعة! سيتم مراجعتها من قبل المشرف.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ: {e}")
            flash(f'❌ حدث خطأ: {str(e)}', 'error')
            return redirect(url_for('submit_word'))

    return render_template('submit_word.html')

@app.route('/debug/submit', methods=['GET', 'POST'])
@login_required
def debug_submit():
    """Page de débogage pour l'ajout de mots"""
    print("\n" + "="*50)
    print("DEBUG SUBMIT - Débogage de l'ajout de mot")
    print("="*50)
    
    print(f"1. User: {current_user.username} (ID: {current_user.id})")
    print(f"2. Authenticated: {current_user.is_authenticated}")
    print(f"3. Method: {request.method}")
    
    if request.method == 'POST':
        print(f"4. Form data reçu:")
        for key, value in request.form.items():
            print(f"   - {key}: {value}")
        
        # Simuler l'ajout
        return "✅ Formulaire reçu avec succès!"
    
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head><title>Debug Submit</title></head>
    <body>
        <h1>Formulaire de test</h1>
        <form method="POST">
            <input type="text" name="word_arabic" placeholder="الكلمة"><br>
            <textarea name="definition" placeholder="التعريف"></textarea><br>
            <button type="submit">Test</button>
        </form>
    </body>
    </html>
    '''
@app.route('/test-link')
def test_link():
    return '<a href="/submit">اذهب إلى إضافة كلمة</a>'
#backup
@app.route('/admin/backup',methods=['GET', 'POST'])
@login_required
def admin_backup():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    import shutil
    from datetime import datetime
    
    # مسار قاعدة البيانات الحالية
    db_path = 'instance/dictionary.db'
    
    # إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # اسم ملف النسخة الاحتياطية مع التاريخ والوقت
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'dictionary_backup_{timestamp}.db')
    
    try:
        # نسخ الملف
        shutil.copy2(db_path, backup_path)
        
        # الحصول على حجم الملف
        file_size = os.path.getsize(backup_path) / 1024  # KB
        
        flash(f'✅ تم إنشاء النسخة الاحتياطية بنجاح! حجم الملف: {file_size:.2f} KB', 'success')
        
        # عرض روابط النسخ الاحتياطية المتوفرة
        backups = []
        for f in os.listdir(backup_dir):
            if f.startswith('dictionary_backup_') and f.endswith('.db'):
                file_path = os.path.join(backup_dir, f)
                stat = os.stat(file_path)
                backups.append({
                    'name': f,
                    'size': stat.st_size / 1024,
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # ترتيب من الأحدث إلى الأقدم
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        return render_template('admin/backup.html', backups=backups)
        
    except Exception as e:
        flash(f'❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/backup/delete/<filename>')
@login_required
def delete_backup(filename):
    """حذف ملف النسخة الاحتياطية"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    import os
    backup_path = os.path.join('backups', filename)
    
    # التأكد من أن الملف موجود
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            flash(f'✅ تم حذف الملف "{filename}" بنجاح', 'success')
        except Exception as e:
            flash(f'❌ حدث خطأ أثناء حذف الملف: {str(e)}', 'error')
    else:
        flash(f'❌ الملف "{filename}" غير موجود', 'error')
    
    return redirect(url_for('admin_backup'))

@app.route('/admin/backup/download/<filename>')
@login_required
def download_backup(filename):
    """تحميل ملف النسخة الاحتياطية"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    from flask import send_file
    backup_path = os.path.join('backups', filename)
    
    if os.path.exists(backup_path):
        return send_file(backup_path, as_attachment=True)
    else:
        flash('❌ الملف غير موجود', 'error')
        return redirect(url_for('admin_backup'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """إعدادات الموقع"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    # جلب الإحصائيات من قاعدة البيانات
    total_words = Word.query.count()
    total_users = User.query.count()
    
    if request.method == 'POST':
        # حفظ الإعدادات (يمكنك إضافة المزيد من الإعدادات هنا)
        site_name = request.form.get('site_name', 'معجم اللهجة التواتية')
        site_description = request.form.get('site_description', 'حفظ وتوثيق الكلمات والتعابير المحلية')
        
        # حفظ في ملف أو قاعدة بيانات (مؤقتاً في session)
        from flask import session
        session['site_name'] = site_name
        session['site_description'] = site_description
        
        flash('✅ تم حفظ الإعدادات بنجاح', 'success')
        return redirect(url_for('admin_settings'))
    
    # GET request - عرض نموذج الإعدادات
    from flask import session
    site_name = session.get('site_name', 'معجم اللهجة التواتية')
    site_description = session.get('site_description', 'حفظ وتوثيق الكلمات والتعابير المحلية')
    
    return render_template('admin/settings.html', 
                          site_name=site_name,
                          site_description=site_description,
                          total_words=total_words,
                          total_users=total_users)

# ===== المقالات =====

@app.route('/articles')
def articles():
    """صفحة عرض المقالات"""
    # قائمة المقالات (مؤقتة - يمكن تخزينها في قاعدة البيانات لاحقاً)
    articles_list = [
        {
            'id': 1,
            'title': 'تاريخ لهجة توات',
            'content': 'لهجة توات هي إحدى اللهجات الجزائرية العريقة التي تتميز بمفرداتها الفريدة...',
            'image': '/static/images/touat.jpg',
            'date': '2024-01-15',
            'author': 'admin'
        },
        {
            'id': 2,
            'title': 'كلمات تواتية أصيلة',
            'content': 'تعرف على أشهر الكلمات التواتية ومعانيها واستخداماتها في الحياة اليومية...',
            'image': '/static/images/touat.jpg',
            'date': '2024-02-20',
            'author': 'admin'
        },
        {
            'id': 3,
            'title': 'أمثال شعبية في توات',
            'content': 'الأمثال الشعبية تعكس حكمة وفكر أهل المنطقة وتوارثها الأجيال...',
            'image': '/static/images/touat.jpg',
            'date': '2024-03-10',
            'author': 'admin'
        }
    ]
    return render_template('articles.html', articles=articles_list)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    """عرض تفاصيل مقالة"""
    # مؤقتاً - يمكن جلب المقالة من قاعدة البيانات
    articles_list = {
        1: {'title': 'تاريخ لهجة توات', 'content': 'لهجة توات هي إحدى اللهجات الجزائرية العريقة...', 'date': '2024-01-15', 'author': 'admin'},
        2: {'title': 'كلمات تواتية أصيلة', 'content': 'تعرف على أشهر الكلمات التواتية...', 'date': '2024-02-20', 'author': 'admin'},
        3: {'title': 'أمثال شعبية في توات', 'content': 'الأمثال الشعبية تعكس حكمة وفكر أهل المنطقة...', 'date': '2024-03-10', 'author': 'admin'}
    }
    article = articles_list.get(article_id)
    if not article:
        flash('❌ المقال غير موجود', 'error')
        return redirect(url_for('articles'))
    return render_template('article_detail.html', article=article, article_id=article_id)


# ===== الفيديوهات =====

@app.route('/videos')
def videos():
    """صفحة عرض الفيديوهات"""
    # قائمة الفيديوهات (مؤقتة)
    videos_list = [
        {
            'id': 1,
            'title': 'تعلم لهجة توات - الدرس الأول',
            'description': 'مقدمة عن لهجة توات والكلمات الأساسية',
            'youtube_id': 'dQw4w9WgXcQ',  # رابط مثال - استبدل برابط فيديو حقيقي
            'thumbnail': '/static/images/video-thumb.jpg',
            'date': '2024-01-20'
        },
        {
            'id': 2,
            'title': 'جولة في منطقة توات',
            'description': 'استكشاف منطقة توات والتعرف على ثقافتها',
            'youtube_id': 'dQw4w9WgXcQ',
            'thumbnail': '/static/images/video-thumb.jpg',
            'date': '2024-02-25'
        },
        {
            'id': 3,
            'title': 'كلمات تواتية في الحياة اليومية',
            'description': 'تعلم كيفية استخدام الكلمات التواتية في المحادثات',
            'youtube_id': 'dQw4w9WgXcQ',
            'thumbnail': '/static/images/video-thumb.jpg',
            'date': '2024-03-15'
        }
    ]
    return render_template('videos.html', videos=videos_list)

@app.route('/video/<int:video_id>')
def video_detail(video_id):
    """عرض تفاصيل فيديو"""
    videos_list = {
        1: {'title': 'تعلم لهجة توات - الدرس الأول', 'description': 'مقدمة عن لهجة توات', 'youtube_id': 'dQw4w9WgXcQ'},
        2: {'title': 'جولة في منطقة توات', 'description': 'استكشاف منطقة توات', 'youtube_id': 'dQw4w9WgXcQ'},
        3: {'title': 'كلمات تواتية في الحياة اليومية', 'description': 'تعلم الكلمات التواتية', 'youtube_id': 'dQw4w9WgXcQ'}
    }
    video = videos_list.get(video_id)
    if not video:
        flash('❌ الفيديو غير موجود', 'error')
        return redirect(url_for('videos'))
    return render_template('video_detail.html', video=video, video_id=video_id)

# ===== DÉTAIL D'UN MOT =====

@app.route('/word/<int:word_id>')
def word_detail(word_id):
    """Page de détail d'un mot"""
    word = Word.query.get_or_404(word_id)
    
    # Mots similaires (même région)
    similar_words = Word.query.filter(
        Word.region == word.region,
        Word.id != word.id
    ).limit(5).all()
    
    return render_template('word_detail.html',
                          word=word,
                          similar_words=similar_words)


@app.route('/debug/word/<word_name>')
def debug_word(word_name):
    from database.models import Word
    word = Word.query.filter_by(word_arabic=word_name).first()
    if word:
        return f"""
        <pre>
        الكلمة: {word.word_arabic}
        الحرف المخزن (arabic_letter): '{word.arabic_letter}'
        طول الحرف: {len(word.arabic_letter) if word.arabic_letter else 0}
        ID: {word.id}
        </pre>
        """
    return f"❌ كلمة '{word_name}' غير موجودة"
# ===== PAGE DE TEST =====

@app.route('/test')
def test_page():
    """Page de test pour vérifier que tout fonctionne"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>اختبار</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>✅ اختبار الوظائف</h1>
        
        <h2>الروابط:</h2>
        <ul>
            <li><a href="/">الصفحة الرئيسية</a></li>
            <li><a href="/search?q=ابرة">بحث: ابرة</a></li>
            <li><a href="/by-letter/أ">حرف الألف</a></li>
            <li><a href="/api/words">API الكلمات</a></li>
            <li><a href="/login">تسجيل الدخول</a></li>
            <li><a href="/register">إنشاء حساب</a></li>
            <li><a href="/admin">لوحة التحكم</a></li>
            <li><a href="/submit">إضافة كلمة</a></li>
            <li><a href="/regions">المناطق</a></li>
        </ul>
        
        <h2>إحصائيات:</h2>
        <p>المستخدمين: {}</p>
        <p>الكلمات: {}</p>
        
        <p><a href="/">العودة</a></p>
    </body>
    </html>
    """.format(User.query.count(), Word.query.count())

@app.route('/admin/view/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """معاينة الطلب قبل الموافقة"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    submission = Submission.query.get_or_404(submission_id)
    return render_template('admin/view_submission.html', submission=submission)


@app.route('/admin/edit/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def edit_submission(submission_id):
    """تعديل الطلب قبل الموافقة"""
    if current_user.role != 'admin':
        flash('⛔ غير مصرح', 'error')
        return redirect(url_for('index'))
    
    submission = Submission.query.get_or_404(submission_id)
    
    if request.method == 'POST':
        submission.word_arabic = request.form.get('word_arabic', '').strip()
        submission.definition = request.form.get('definition', '').strip()
        submission.region = request.form.get('region', 'توات').strip()
        submission.example = request.form.get('example', '').strip()
        submission.category = request.form.get('category', '').strip()
        # معالجة الصورة الجديدة
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_path = save_file(image_file, UPLOAD_FOLDER_IMAGES, ALLOWED_EXTENSIONS_IMAGES)
            if image_path:
                submission.image_path = image_path
        
        # معالجة الصوت الجديد
        audio_file = request.files.get('audio')
        if audio_file and audio_file.filename:
            audio_path = save_file(audio_file, UPLOAD_FOLDER_AUDIO, ALLOWED_EXTENSIONS_AUDIO)
            if audio_path:
                submission.audio_path = audio_path
        
        db.session.commit()
        flash('✅ تم تعديل الطلب بنجاح', 'success')
        return redirect(url_for('admin_submissions'))
    
    return render_template('admin/edit_submission.html', submission=submission)

# ===== PAGE 404 =====

@app.errorhandler(404)
def page_not_found(e):
    """Page 404 personnalisée"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>404 - غير موجود</title></head>
    <body style="font-family: Arial; padding: 40px; text-align: center;">
        <h1>❌ 404 - الصفحة غير موجودة</h1>
        <p>الصفحة التي تبحث عنها غير موجودة.</p>
        <p><a href="/">العودة للصفحة الرئيسية</a></p>
    </body>
    </html>
    """, 404

# ===== DÉMARRAGE =====

if __name__ == '__main__':
    print("🚀 معجم اللهجة التواتية")
    print("🌐 http://localhost:5000")
    print("🔑 Admin: admin@touat.com / admin123")
    print("🔗 Test: http://localhost:5000/test")
    app.run(debug=True, port=5000)

