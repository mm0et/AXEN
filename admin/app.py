"""
AXEN - Admin Panel (WordPress-style CMS)
=========================================
Panel de administración completo para gestionar el contenido
del landing page corporativo de AXEN.
"""

import os
import json
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_from_directory, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── App Config ──────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'axen-admin-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///axen_cms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the admin panel.'
login_manager.login_message_category = 'warning'


# ── Models ──────────────────────────────────────────────────
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), default='Admin')
    role = db.Column(db.String(20), default='admin')  # admin, editor
    avatar = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(200), default='AXEN')
    site_tagline = db.Column(db.String(300), default='Secure Your Digital World')
    site_email = db.Column(db.String(120), default='info@axen.es')
    site_phone = db.Column(db.String(50), default='+34 912 345 678')
    site_address = db.Column(db.String(300), default='Calle Gran Vía 123, Madrid, España')
    logo_url = db.Column(db.String(300), default='')
    favicon_url = db.Column(db.String(300), default='')
    facebook = db.Column(db.String(200), default='#')
    twitter = db.Column(db.String(200), default='#')
    linkedin = db.Column(db.String(200), default='#')
    instagram = db.Column(db.String(200), default='#')
    youtube = db.Column(db.String(200), default='#')
    footer_text = db.Column(db.String(500), default='© 2025 AXEN. Todos los derechos reservados.')
    analytics_code = db.Column(db.Text, default='')
    custom_css = db.Column(db.Text, default='')
    custom_js = db.Column(db.Text, default='')
    maintenance_mode = db.Column(db.Boolean, default=False)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # hero, features, servers, etc.
    title = db.Column(db.String(300), default='')
    subtitle = db.Column(db.String(500), default='')
    content = db.Column(db.Text, default='')
    is_visible = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    settings_json = db.Column(db.Text, default='{}')  # Extra config
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def settings(self):
        try:
            return json.loads(self.settings_json) if self.settings_json else {}
        except json.JSONDecodeError:
            return {}

    @settings.setter
    def settings(self, value):
        self.settings_json = json.dumps(value)


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(100), default='fas fa-star')
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


class PricingPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(5), default='€')
    period = db.Column(db.String(20), default='/month')
    features_json = db.Column(db.Text, default='[]')
    is_featured = db.Column(db.Boolean, default=False)
    badge_text = db.Column(db.String(50), default='')
    button_text = db.Column(db.String(50), default='Get Started')
    button_url = db.Column(db.String(300), default='#')
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)

    @property
    def features_list(self):
        try:
            return json.loads(self.features_json) if self.features_json else []
        except json.JSONDecodeError:
            return []

    @features_list.setter
    def features_list(self, value):
        self.features_json = json.dumps(value)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), default='')
    content = db.Column(db.Text, default='')
    rating = db.Column(db.Integer, default=5)
    avatar = db.Column(db.String(300), default='')
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


class ServerLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    flag_emoji = db.Column(db.String(10), default='🌍')
    server_count = db.Column(db.Integer, default=0)
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


class MediaFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(300), default='')
    file_type = db.Column(db.String(20), default='image')
    file_size = db.Column(db.Integer, default=0)
    alt_text = db.Column(db.String(300), default='')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def url(self):
        return f'/admin/static/uploads/{self.filename}'


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── Login Manager ───────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Helper Functions ────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings


def init_default_data():
    """Populate database with default content on first run."""
    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@axen.es',
            display_name='Administrator',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

    if SiteSettings.query.count() == 0:
        db.session.add(SiteSettings())

    if Section.query.count() == 0:
        default_sections = [
            Section(name='hero', title='Transformamos tu infraestructura en ventaja competitiva',
                    subtitle='Infraestructura, Cloud, Automatización e IA',
                    content='Diseñamos, construimos y operamos entornos cloud, automatización e inteligencia artificial para empresas que necesitan escalar sin fricciones.',
                    order_index=1),
            Section(name='services', title='Lo que hacemos',
                    subtitle='Soluciones integrales de infraestructura y tecnología.',
                    order_index=2),
            Section(name='about', title='Ingeniería de infraestructura con visión de negocio',
                    subtitle='Sobre AXEN',
                    order_index=3),
            Section(name='solutions', title='Tecnología que se adapta a tu escala',
                    subtitle='Desde startups hasta grandes corporaciones.',
                    order_index=4),
            Section(name='testimonials', title='Lo que dicen de nosotros',
                    subtitle='La confianza de nuestros clientes es nuestro mejor indicador.',
                    order_index=4),
            Section(name='pricing', title='Choose Your Perfect Plan',
                    subtitle='Simple, transparent pricing. No hidden fees.',
                    order_index=5),
            Section(name='contact', title='Hablemos de tu proyecto',
                    subtitle='Escríbenos y te respondemos en menos de 24 horas.',
                    order_index=6),
        ]
        db.session.add_all(default_sections)

    if Feature.query.count() == 0:
        defaults = [
            Feature(icon='fas fa-cloud', title='Cloud & Hybrid Infrastructure',
                    description='Diseño, migración y gestión de entornos cloud en AWS, Azure y Google Cloud.', order_index=1),
            Feature(icon='fas fa-gears', title='Automatización & DevOps',
                    description='CI/CD pipelines, Infrastructure as Code con Terraform y Ansible.', order_index=2),
            Feature(icon='fas fa-brain', title='Inteligencia Artificial',
                    description='Implementación de modelos de IA, MLOps y soluciones de machine learning.', order_index=3),
            Feature(icon='fas fa-shield-halved', title='Ciberseguridad',
                    description='Auditorías de seguridad, Zero Trust, SIEM y respuesta ante incidentes.', order_index=4),
            Feature(icon='fas fa-chart-line', title='Monitorización & Observabilidad',
                    description='Stacks de observabilidad con Prometheus, Grafana y ELK.', order_index=5),
            Feature(icon='fas fa-network-wired', title='Consultoría IT',
                    description='Estrategia tecnológica, arquitectura de soluciones y roadmaps de transformación digital.', order_index=6),
        ]
        db.session.add_all(defaults)

    if PricingPlan.query.count() == 0:
        plans = [
            PricingPlan(name='Basic', price=4.99, features_json=json.dumps([
                {'text': '1 Device', 'included': True},
                {'text': '50+ Server Locations', 'included': True},
                {'text': 'Standard Encryption', 'included': True},
                {'text': 'Email Support', 'included': True},
                {'text': 'Kill Switch', 'included': False},
                {'text': 'Dedicated IP', 'included': False},
            ]), order_index=1),
            PricingPlan(name='Professional', price=9.99, is_featured=True,
                        badge_text='Most Popular', features_json=json.dumps([
                {'text': '5 Devices', 'included': True},
                {'text': '100+ Server Locations', 'included': True},
                {'text': 'AES-256 Encryption', 'included': True},
                {'text': '24/7 Priority Support', 'included': True},
                {'text': 'Kill Switch', 'included': True},
                {'text': 'Dedicated IP', 'included': False},
            ]), order_index=2),
            PricingPlan(name='Enterprise', price=14.99, features_json=json.dumps([
                {'text': '10 Devices', 'included': True},
                {'text': 'All Server Locations', 'included': True},
                {'text': 'AES-256 Encryption', 'included': True},
                {'text': '24/7 VIP Support', 'included': True},
                {'text': 'Kill Switch', 'included': True},
                {'text': 'Dedicated IP', 'included': True},
            ]), order_index=3),
        ]
        db.session.add_all(plans)

    if Testimonial.query.count() == 0:
        testimonials = [
            Testimonial(name='Carlos Martínez', role='CTO · TechCorp', rating=5,
                        content='AXEN migró toda nuestra infraestructura a AWS en 3 meses sin una sola hora de downtime.', order_index=1),
            Testimonial(name='Laura Rodríguez', role='VP Engineering · FinBank', rating=5,
                        content='Implementaron nuestro pipeline CI/CD completo. Despliegues automáticos en 8 minutos.', order_index=2),
            Testimonial(name='Andrés García', role='SysAdmin Lead · LogiMove', rating=5,
                        content='Gracias a AXEN tenemos visibilidad total de nuestra infraestructura.', order_index=3),
            Testimonial(name='María Pérez', role='Directora IT · MedixPro', rating=5,
                        content='La solución de IA redujo el tiempo de respuesta de nuestro triaje de tickets un 60%.', order_index=4),
        ]
        db.session.add_all(testimonials)

    if ServerLocation.query.count() == 0:
        servers = [
            ServerLocation(country='United States', flag_emoji='🇺🇸', server_count=150, order_index=1),
            ServerLocation(country='United Kingdom', flag_emoji='🇬🇧', server_count=80, order_index=2),
            ServerLocation(country='Germany', flag_emoji='🇩🇪', server_count=60, order_index=3),
            ServerLocation(country='Japan', flag_emoji='🇯🇵', server_count=45, order_index=4),
            ServerLocation(country='Spain', flag_emoji='🇪🇸', server_count=40, order_index=5),
            ServerLocation(country='Australia', flag_emoji='🇦🇺', server_count=35, order_index=6),
        ]
        db.session.add_all(servers)

    db.session.commit()


# ── Auth Routes ─────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=True)
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ── Dashboard ───────────────────────────────────────────────
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'sections': Section.query.count(),
        'features': Feature.query.count(),
        'plans': PricingPlan.query.count(),
        'testimonials': Testimonial.query.count(),
        'servers': ServerLocation.query.count(),
        'media': MediaFile.query.count(),
        'messages': ContactMessage.query.filter_by(is_read=False).count(),
        'users': User.query.count(),
    }
    recent_messages = ContactMessage.query.order_by(
        ContactMessage.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, recent_messages=recent_messages)


# ── Sections ────────────────────────────────────────────────
@app.route('/sections')
@login_required
def sections_list():
    sections = Section.query.order_by(Section.order_index).all()
    return render_template('sections.html', sections=sections)


@app.route('/sections/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def section_edit(id):
    section = Section.query.get_or_404(id)
    if request.method == 'POST':
        section.title = request.form.get('title', '')
        section.subtitle = request.form.get('subtitle', '')
        section.content = request.form.get('content', '')
        section.is_visible = 'is_visible' in request.form
        db.session.commit()
        flash(f'Section "{section.name}" updated successfully!', 'success')
        return redirect(url_for('sections_list'))
    return render_template('section_edit.html', section=section)


# ── Features ────────────────────────────────────────────────
@app.route('/features')
@login_required
def features_list():
    features = Feature.query.order_by(Feature.order_index).all()
    return render_template('features.html', features=features)


@app.route('/features/new', methods=['GET', 'POST'])
@app.route('/features/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def feature_edit(id=None):
    feature = Feature.query.get(id) if id else None
    if request.method == 'POST':
        if not feature:
            feature = Feature()
            db.session.add(feature)
        feature.icon = request.form.get('icon', 'fas fa-star')
        feature.title = request.form.get('title', '')
        feature.description = request.form.get('description', '')
        feature.order_index = int(request.form.get('order_index', 0))
        feature.is_visible = 'is_visible' in request.form
        db.session.commit()
        flash('Feature saved successfully!', 'success')
        return redirect(url_for('features_list'))
    return render_template('feature_edit.html', feature=feature)


@app.route('/features/<int:id>/delete', methods=['POST'])
@login_required
def feature_delete(id):
    feature = Feature.query.get_or_404(id)
    db.session.delete(feature)
    db.session.commit()
    flash('Feature deleted.', 'info')
    return redirect(url_for('features_list'))


# ── Pricing Plans ───────────────────────────────────────────
@app.route('/pricing')
@login_required
def pricing_list():
    plans = PricingPlan.query.order_by(PricingPlan.order_index).all()
    return render_template('pricing.html', plans=plans)


@app.route('/pricing/new', methods=['GET', 'POST'])
@app.route('/pricing/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def pricing_edit(id=None):
    plan = PricingPlan.query.get(id) if id else None
    if request.method == 'POST':
        if not plan:
            plan = PricingPlan()
            db.session.add(plan)
        plan.name = request.form.get('name', '')
        plan.price = float(request.form.get('price', 0))
        plan.currency = request.form.get('currency', '€')
        plan.period = request.form.get('period', '/month')
        plan.badge_text = request.form.get('badge_text', '')
        plan.button_text = request.form.get('button_text', 'Get Started')
        plan.button_url = request.form.get('button_url', '#')
        plan.is_featured = 'is_featured' in request.form
        plan.is_visible = 'is_visible' in request.form
        plan.order_index = int(request.form.get('order_index', 0))
        # Parse features
        features = []
        feat_texts = request.form.getlist('feat_text')
        feat_included = request.form.getlist('feat_included')
        for i, text in enumerate(feat_texts):
            if text.strip():
                features.append({
                    'text': text.strip(),
                    'included': str(i) in feat_included
                })
        plan.features_json = json.dumps(features)
        db.session.commit()
        flash('Plan saved successfully!', 'success')
        return redirect(url_for('pricing_list'))
    return render_template('pricing_edit.html', plan=plan)


@app.route('/pricing/<int:id>/delete', methods=['POST'])
@login_required
def pricing_delete(id):
    plan = PricingPlan.query.get_or_404(id)
    db.session.delete(plan)
    db.session.commit()
    flash('Plan deleted.', 'info')
    return redirect(url_for('pricing_list'))


# ── Testimonials ────────────────────────────────────────────
@app.route('/testimonials')
@login_required
def testimonials_list():
    testimonials = Testimonial.query.order_by(Testimonial.order_index).all()
    return render_template('testimonials.html', testimonials=testimonials)


@app.route('/testimonials/new', methods=['GET', 'POST'])
@app.route('/testimonials/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def testimonial_edit(id=None):
    testimonial = Testimonial.query.get(id) if id else None
    if request.method == 'POST':
        if not testimonial:
            testimonial = Testimonial()
            db.session.add(testimonial)
        testimonial.name = request.form.get('name', '')
        testimonial.role = request.form.get('role', '')
        testimonial.content = request.form.get('content', '')
        testimonial.rating = int(request.form.get('rating', 5))
        testimonial.order_index = int(request.form.get('order_index', 0))
        testimonial.is_visible = 'is_visible' in request.form
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename and allowed_file(file.filename):
                filename = f"avatar_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                testimonial.avatar = filename
        db.session.commit()
        flash('Testimonial saved successfully!', 'success')
        return redirect(url_for('testimonials_list'))
    return render_template('testimonial_edit.html', testimonial=testimonial)


@app.route('/testimonials/<int:id>/delete', methods=['POST'])
@login_required
def testimonial_delete(id):
    t = Testimonial.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Testimonial deleted.', 'info')
    return redirect(url_for('testimonials_list'))


# ── Server Locations ────────────────────────────────────────
@app.route('/servers')
@login_required
def servers_list():
    servers = ServerLocation.query.order_by(ServerLocation.order_index).all()
    return render_template('servers.html', servers=servers)


@app.route('/servers/new', methods=['GET', 'POST'])
@app.route('/servers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def server_edit(id=None):
    server = ServerLocation.query.get(id) if id else None
    if request.method == 'POST':
        if not server:
            server = ServerLocation()
            db.session.add(server)
        server.country = request.form.get('country', '')
        server.flag_emoji = request.form.get('flag_emoji', '🌍')
        server.server_count = int(request.form.get('server_count', 0))
        server.order_index = int(request.form.get('order_index', 0))
        server.is_visible = 'is_visible' in request.form
        db.session.commit()
        flash('Server location saved!', 'success')
        return redirect(url_for('servers_list'))
    return render_template('server_edit.html', server=server)


@app.route('/servers/<int:id>/delete', methods=['POST'])
@login_required
def server_delete(id):
    s = ServerLocation.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash('Server location deleted.', 'info')
    return redirect(url_for('servers_list'))


# ── Media Library ───────────────────────────────────────────
@app.route('/media')
@login_required
def media_library():
    files = MediaFile.query.order_by(MediaFile.uploaded_at.desc()).all()
    return render_template('media.html', files=files)


@app.route('/media/upload', methods=['POST'])
@login_required
def media_upload():
    if 'file' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('media_library'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('media_library'))
    if file and allowed_file(file.filename):
        original = file.filename
        filename = f"{uuid.uuid4().hex[:8]}_{secure_filename(original)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        media = MediaFile(
            filename=filename,
            original_name=original,
            file_size=os.path.getsize(filepath),
            uploaded_by=current_user.id,
            alt_text=request.form.get('alt_text', '')
        )
        db.session.add(media)
        db.session.commit()
        flash('File uploaded successfully!', 'success')
    else:
        flash('File type not allowed.', 'danger')
    return redirect(url_for('media_library'))


@app.route('/media/<int:id>/delete', methods=['POST'])
@login_required
def media_delete(id):
    media = MediaFile.query.get_or_404(id)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], media.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(media)
    db.session.commit()
    flash('File deleted.', 'info')
    return redirect(url_for('media_library'))


# ── Messages ───────────────────────────────────────────────
@app.route('/messages')
@login_required
def messages_list():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('messages.html', messages=messages)


@app.route('/messages/<int:id>')
@login_required
def message_view(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return render_template('message_view.html', msg=msg)


@app.route('/messages/<int:id>/delete', methods=['POST'])
@login_required
def message_delete(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('messages_list'))


# ── Settings ───────────────────────────────────────────────
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    site = get_settings()
    if request.method == 'POST':
        site.site_name = request.form.get('site_name', site.site_name)
        site.site_tagline = request.form.get('site_tagline', site.site_tagline)
        site.site_email = request.form.get('site_email', site.site_email)
        site.site_phone = request.form.get('site_phone', site.site_phone)
        site.site_address = request.form.get('site_address', site.site_address)
        site.facebook = request.form.get('facebook', '#')
        site.twitter = request.form.get('twitter', '#')
        site.linkedin = request.form.get('linkedin', '#')
        site.instagram = request.form.get('instagram', '#')
        site.youtube = request.form.get('youtube', '#')
        site.footer_text = request.form.get('footer_text', '')
        site.analytics_code = request.form.get('analytics_code', '')
        site.custom_css = request.form.get('custom_css', '')
        site.custom_js = request.form.get('custom_js', '')
        site.maintenance_mode = 'maintenance_mode' in request.form
        db.session.commit()
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', site=site)


# ── Users ──────────────────────────────────────────────────
@app.route('/users')
@login_required
def users_list():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/users/new', methods=['GET', 'POST'])
@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(id=None):
    user = User.query.get(id) if id else None
    if request.method == 'POST':
        if not user:
            user = User()
            db.session.add(user)
        user.username = request.form.get('username', '')
        user.email = request.form.get('email', '')
        user.display_name = request.form.get('display_name', '')
        user.role = request.form.get('role', 'editor')
        password = request.form.get('password', '')
        if password:
            user.set_password(password)
        db.session.commit()
        flash('User saved successfully!', 'success')
        return redirect(url_for('users_list'))
    return render_template('user_edit.html', user=user)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.display_name = request.form.get('display_name', '')
        current_user.email = request.form.get('email', '')
        new_password = request.form.get('new_password', '')
        if new_password:
            current_user.set_password(new_password)
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')


# ── API: Contact form (from landing page) ──────────────────
@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.get_json() or request.form
    msg = ContactMessage(
        name=data.get('name', ''),
        email=data.get('email', ''),
        subject=data.get('subject', ''),
        message=data.get('message', '')
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Message received!'})


# ── API: Get site content (for landing page dynamic loading) ──
@app.route('/api/content')
def api_content():
    sections = Section.query.filter_by(is_visible=True).order_by(Section.order_index).all()
    features = Feature.query.filter_by(is_visible=True).order_by(Feature.order_index).all()
    plans = PricingPlan.query.filter_by(is_visible=True).order_by(PricingPlan.order_index).all()
    testimonials = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.order_index).all()
    servers = ServerLocation.query.filter_by(is_visible=True).order_by(ServerLocation.order_index).all()
    site = get_settings()

    return jsonify({
        'site': {
            'name': site.site_name,
            'tagline': site.site_tagline,
            'email': site.site_email,
            'phone': site.site_phone,
            'address': site.site_address,
        },
        'sections': [{'name': s.name, 'title': s.title, 'subtitle': s.subtitle, 'content': s.content} for s in sections],
        'features': [{'icon': f.icon, 'title': f.title, 'description': f.description} for f in features],
        'plans': [{'name': p.name, 'price': p.price, 'currency': p.currency, 'period': p.period,
                    'features': p.features_list, 'is_featured': p.is_featured, 'badge': p.badge_text} for p in plans],
        'testimonials': [{'name': t.name, 'role': t.role, 'content': t.content, 'rating': t.rating} for t in testimonials],
        'servers': [{'country': s.country, 'flag': s.flag_emoji, 'count': s.server_count} for s in servers],
    })


# ── Main ───────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    init_default_data()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
