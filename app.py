from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import os, io, csv, bleach, qrcode, json
from models import db, Officer, PoliceStation, Feedback, Notification, AuditLog
from config import config

app = Flask(__name__)
app.config.from_object(config['development'])

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize(text):
    return bleach.clean(text, tags=[], strip=True) if text else text

def log_action(action, details=None):
    if current_user.is_authenticated:
        log = AuditLog(
            officer_id=current_user.id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return Officer.query.get(int(user_id))

# ─── PUBLIC ROUTES ──────────────────────────────────────────────

@app.route('/')
def index():
    total_feedback = Feedback.query.count()
    total_stations = PoliceStation.query.filter_by(is_active=True).count()
    avg_rating = db.session.query(func.avg(Feedback.overall_rating)).scalar() or 0
    resolved = Feedback.query.filter_by(is_resolved=True).count()
    stations = PoliceStation.query.filter_by(is_active=True).limit(6).all()
    return render_template('index.html',
        total_feedback=total_feedback,
        total_stations=total_stations,
        avg_rating=round(float(avg_rating), 1),
        resolved=resolved,
        stations=stations
    )

@app.route('/feedback/<station_code>', methods=['GET', 'POST'])
def feedback_form(station_code):
    station = PoliceStation.query.filter_by(station_code=station_code, is_active=True).first_or_404()
    if request.method == 'POST':
        try:
            ack_id = Feedback.generate_ack_id()
            while Feedback.query.filter_by(acknowledgment_id=ack_id).first():
                ack_id = Feedback.generate_ack_id()

            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{ack_id}_{file.filename}")
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_path = f"uploads/{filename}"

            fb = Feedback(
                station_id=station.id,
                acknowledgment_id=ack_id,
                citizen_name=sanitize(request.form.get('citizen_name')),
                mobile=sanitize(request.form.get('mobile')),
                gender=request.form.get('gender'),
                age_group=request.form.get('age_group'),
                behavior_rating=int(request.form.get('behavior_rating', 0)) or None,
                response_rating=int(request.form.get('response_rating', 0)) or None,
                cleanliness_rating=int(request.form.get('cleanliness_rating', 0)) or None,
                helpfulness_rating=int(request.form.get('helpfulness_rating', 0)) or None,
                transparency_rating=int(request.form.get('transparency_rating', 0)) or None,
                overall_rating=int(request.form.get('overall_rating', 0)) or None,
                feedback_text=sanitize(request.form.get('feedback_text')),
                complaint=sanitize(request.form.get('complaint')),
                complaint_category=request.form.get('complaint_category') or None,
                image_path=image_path,
                ip_address=request.remote_addr
            )
            fb.analyze_sentiment()
            db.session.add(fb)

            # Notify officers
            officers = Officer.query.filter_by(station_id=station.id, is_active=True).all()
            for officer in officers:
                notif = Notification(
                    officer_id=officer.id,
                    message=f"New feedback received for {station.station_name} (ID: {ack_id})",
                    type='complaint' if fb.complaint else 'feedback'
                )
                db.session.add(notif)

            db.session.commit()
            return jsonify({'success': True, 'ack_id': ack_id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    return render_template('citizen/feedback_form.html', station=station)

@app.route('/feedback/success/<ack_id>')
def feedback_success(ack_id):
    return render_template('citizen/success.html', ack_id=ack_id)

# ─── AUTH ROUTES ────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        officer = Officer.query.filter_by(email=email, is_active=True).first()
        if officer and officer.check_password(password):
            login_user(officer, remember=request.form.get('remember'))
            officer.last_login = datetime.utcnow()
            db.session.commit()
            log_action('LOGIN', f'Officer {officer.name} logged in')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    log_action('LOGOUT')
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ─── DASHBOARD ──────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    month_ago = datetime.utcnow() - timedelta(days=30)

    query = Feedback.query
    if not current_user.is_admin() and current_user.station_id:
        query = query.filter_by(station_id=current_user.station_id)

    total = query.count()
    today_count = query.filter(func.date(Feedback.submitted_at) == today).count()
    avg_rating = db.session.query(func.avg(Feedback.overall_rating)).scalar() or 0
    complaints = query.filter(Feedback.complaint != None, Feedback.complaint != '').count()
    resolved = query.filter_by(is_resolved=True).count()
    positive = query.filter_by(sentiment='positive').count()
    negative = query.filter_by(sentiment='negative').count()

    # Weekly trend
    weekly_data = []
    for i in range(7):
        day = datetime.utcnow().date() - timedelta(days=6-i)
        count = query.filter(func.date(Feedback.submitted_at) == day).count()
        weekly_data.append({'day': day.strftime('%a'), 'count': count})

    # Rating distribution
    rating_dist = []
    for r in range(1, 6):
        count = query.filter_by(overall_rating=r).count()
        rating_dist.append(count)

    # Station performance (admin only)
    station_perf = []
    if current_user.is_admin():
        stations = PoliceStation.query.filter_by(is_active=True).all()
        for s in stations:
            avg = db.session.query(func.avg(Feedback.overall_rating))\
                .filter_by(station_id=s.id).scalar() or 0
            cnt = Feedback.query.filter_by(station_id=s.id).count()
            station_perf.append({'name': s.station_name[:20], 'avg': round(float(avg), 1), 'count': cnt})

    recent = query.order_by(desc(Feedback.submitted_at)).limit(10).all()
    notifications = Notification.query.filter_by(officer_id=current_user.id, is_read=False)\
        .order_by(desc(Notification.created_at)).limit(5).all()

    return render_template('admin/dashboard.html',
        total=total, today_count=today_count,
        avg_rating=round(float(avg_rating), 1),
        complaints=complaints, resolved=resolved,
        positive=positive, negative=negative,
        weekly_data=json.dumps(weekly_data),
        rating_dist=json.dumps(rating_dist),
        station_perf=json.dumps(station_perf),
        recent=recent, notifications=notifications
    )

# ─── FEEDBACK MANAGEMENT ────────────────────────────────────────

@app.route('/feedbacks')
@login_required
def feedbacks():
    page = request.args.get('page', 1, type=int)
    station_id = request.args.get('station_id', type=int)
    rating = request.args.get('rating', type=int)
    sentiment = request.args.get('sentiment')
    search = request.args.get('search', '')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = Feedback.query
    if not current_user.is_admin() and current_user.station_id:
        query = query.filter_by(station_id=current_user.station_id)
    if station_id and current_user.is_admin():
        query = query.filter_by(station_id=station_id)
    if rating:
        query = query.filter_by(overall_rating=rating)
    if sentiment:
        query = query.filter_by(sentiment=sentiment)
    if search:
        query = query.filter(
            Feedback.citizen_name.contains(search) |
            Feedback.feedback_text.contains(search) |
            Feedback.acknowledgment_id.contains(search)
        )
    if date_from:
        query = query.filter(Feedback.submitted_at >= date_from)
    if date_to:
        query = query.filter(Feedback.submitted_at <= date_to + ' 23:59:59')

    feedbacks = query.order_by(desc(Feedback.submitted_at)).paginate(page=page, per_page=20, error_out=False)
    stations = PoliceStation.query.filter_by(is_active=True).all() if current_user.is_admin() else []
    notifications = Notification.query.filter_by(officer_id=current_user.id, is_read=False).count()

    return render_template('admin/feedbacks.html',
        feedbacks=feedbacks, stations=stations, notifications=notifications)

@app.route('/feedback/resolve/<int:fb_id>', methods=['POST'])
@login_required
def resolve_feedback(fb_id):
    fb = Feedback.query.get_or_404(fb_id)
    fb.is_resolved = True
    fb.resolved_by = current_user.id
    fb.resolved_at = datetime.utcnow()
    fb.resolution_note = sanitize(request.form.get('note', ''))
    db.session.commit()
    log_action('RESOLVE_FEEDBACK', f'Resolved feedback {fb.acknowledgment_id}')
    return jsonify({'success': True})

@app.route('/feedback/flag/<int:fb_id>', methods=['POST'])
@login_required
def flag_feedback(fb_id):
    fb = Feedback.query.get_or_404(fb_id)
    fb.is_flagged = not fb.is_flagged
    db.session.commit()
    return jsonify({'success': True, 'flagged': fb.is_flagged})

@app.route('/feedback/delete/<int:fb_id>', methods=['POST'])
@login_required
def delete_feedback(fb_id):
    if not current_user.is_admin():
        abort(403)
    fb = Feedback.query.get_or_404(fb_id)
    log_action('DELETE_FEEDBACK', f'Deleted feedback {fb.acknowledgment_id}')
    db.session.delete(fb)
    db.session.commit()
    return jsonify({'success': True})

# ─── STATIONS ───────────────────────────────────────────────────

@app.route('/stations')
@login_required
def stations():
    if not current_user.is_admin():
        abort(403)
    stations = PoliceStation.query.all()
    notifications = Notification.query.filter_by(officer_id=current_user.id, is_read=False).count()
    return render_template('admin/stations.html', stations=stations, notifications=notifications)

@app.route('/stations/add', methods=['POST'])
@login_required
def add_station():
    if not current_user.is_admin():
        abort(403)
    station = PoliceStation(
        station_name=sanitize(request.form.get('station_name')),
        district=sanitize(request.form.get('district')),
        address=sanitize(request.form.get('address')),
        contact_number=sanitize(request.form.get('contact_number')),
        station_code=sanitize(request.form.get('station_code', '').upper())
    )
    db.session.add(station)
    db.session.flush()
    generate_qr_for_station(station)
    db.session.commit()
    log_action('ADD_STATION', f'Added station {station.station_name}')
    return jsonify({'success': True, 'id': station.id})

@app.route('/stations/qr/<int:station_id>')
@login_required
def get_station_qr(station_id):
    station = PoliceStation.query.get_or_404(station_id)
    if station.qr_code_path and os.path.exists(os.path.join(app.root_path, 'static', station.qr_code_path)):
        return send_file(os.path.join(app.root_path, 'static', station.qr_code_path),
                        mimetype='image/png', as_attachment=True,
                        download_name=f"QR_{station.station_code}.png")
    return jsonify({'error': 'QR not found'}), 404

def generate_qr_for_station(station):
    feedback_url = f"{app.config['BASE_URL']}/feedback/{station.station_code}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(feedback_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1a237e', back_color='white')
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
    path = os.path.join(app.config['QR_FOLDER'], f"{station.station_code}.png")
    img.save(path)
    station.qr_code_path = f"qr_codes/{station.station_code}.png"
    station.qr_code_url = feedback_url

# ─── OFFICERS ───────────────────────────────────────────────────

@app.route('/officers')
@login_required
def officers():
    if not current_user.is_admin():
        abort(403)
    officers = Officer.query.all()
    stations = PoliceStation.query.filter_by(is_active=True).all()
    notifications = Notification.query.filter_by(officer_id=current_user.id, is_read=False).count()
    return render_template('admin/officers.html', officers=officers, stations=stations, notifications=notifications)

@app.route('/officers/add', methods=['POST'])
@login_required
def add_officer():
    if not current_user.is_admin():
        abort(403)
    officer = Officer(
        name=sanitize(request.form.get('name')),
        badge_number=sanitize(request.form.get('badge_number')),
        email=sanitize(request.form.get('email', '').lower()),
        role=request.form.get('role', 'officer'),
        station_id=request.form.get('station_id') or None,
        phone=sanitize(request.form.get('phone')),
        rank=sanitize(request.form.get('rank'))
    )
    officer.set_password(request.form.get('password'))
    db.session.add(officer)
    db.session.commit()
    log_action('ADD_OFFICER', f'Added officer {officer.name}')
    return jsonify({'success': True})

# ─── REPORTS & EXPORTS ──────────────────────────────────────────

@app.route('/export/csv')
@login_required
def export_csv():
    query = Feedback.query
    if not current_user.is_admin() and current_user.station_id:
        query = query.filter_by(station_id=current_user.station_id)
    feedbacks = query.order_by(desc(Feedback.submitted_at)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ack ID', 'Station', 'Name', 'Gender', 'Age Group',
                     'Behavior', 'Response', 'Cleanliness', 'Helpfulness',
                     'Transparency', 'Overall', 'Sentiment', 'Feedback', 'Complaint', 'Date'])
    for f in feedbacks:
        writer.writerow([
            f.acknowledgment_id, f.station.station_name if f.station else '',
            f.citizen_name or 'Anonymous', f.gender or '', f.age_group or '',
            f.behavior_rating, f.response_rating, f.cleanliness_rating,
            f.helpfulness_rating, f.transparency_rating, f.overall_rating,
            f.sentiment or '', f.feedback_text or '', f.complaint or '',
            f.submitted_at.strftime('%Y-%m-%d %H:%M')
        ])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                    mimetype='text/csv', as_attachment=True,
                    download_name=f'feedback_export_{datetime.utcnow().strftime("%Y%m%d")}.csv')

# ─── API ENDPOINTS ───────────────────────────────────────────────

@app.route('/api/stats')
@login_required
def api_stats():
    query = Feedback.query
    if not current_user.is_admin() and current_user.station_id:
        query = query.filter_by(station_id=current_user.station_id)
    return jsonify({
        'total': query.count(),
        'positive': query.filter_by(sentiment='positive').count(),
        'negative': query.filter_by(sentiment='negative').count(),
        'avg_rating': float(db.session.query(func.avg(Feedback.overall_rating)).scalar() or 0)
    })

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(officer_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

# ─── INIT ────────────────────────────────────────────────────────

@app.cli.command('init-db')
def init_db():
    db.create_all()
    if not Officer.query.filter_by(email='admin@gujaratpolice.gov.in').first():
        admin = Officer(
            name='System Administrator',
            badge_number='ADMIN001',
            email='admin@gujaratpolice.gov.in',
            role='admin',
            rank='Inspector General'
        )
        admin.set_password('Admin@1234')
        db.session.add(admin)

        stations_data = [
            ('Ahmedabad City Police Station', 'Ahmedabad', 'Shahibaug, Ahmedabad - 380004', '079-25621234', 'AMD001'),
            ('Surat Central Police Station', 'Surat', 'Ring Road, Surat - 395002', '0261-2422234', 'SRT001'),
            ('Vadodara Sayajigunj Police Station', 'Vadodara', 'Sayajigunj, Vadodara - 390005', '0265-2363234', 'VDR001'),
            ('Rajkot Police Station', 'Rajkot', 'Dr. Yagnik Road, Rajkot - 360001', '0281-2236234', 'RJT001'),
            ('Gandhinagar Sector-7 Police Station', 'Gandhinagar', 'Sector-7, Gandhinagar - 382007', '079-23222234', 'GDN001'),
        ]
        for data in stations_data:
            s = PoliceStation(station_name=data[0], district=data[1], address=data[2],
                            contact_number=data[3], station_code=data[4])
            db.session.add(s)
            db.session.flush()
            generate_qr_for_station(s)

        db.session.commit()
        print('✅ Database initialized with demo data!')
        print('📧 Admin email: admin@gujaratpolice.gov.in')
        print('🔑 Admin password: Admin@1234')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
