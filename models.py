from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random, string

db = SQLAlchemy()

class PoliceStation(db.Model):
    __tablename__ = 'police_stations'
    id = db.Column(db.Integer, primary_key=True)
    station_name = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    contact_number = db.Column(db.String(15))
    station_code = db.Column(db.String(20), unique=True, nullable=False)
    qr_code_path = db.Column(db.String(500))
    qr_code_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    feedbacks = db.relationship('Feedback', backref='station', lazy='dynamic')
    officers = db.relationship('Officer', backref='station', lazy='dynamic')

    def avg_rating(self):
        feedbacks = self.feedbacks.all()
        if not feedbacks:
            return 0
        total = sum(f.overall_rating or 0 for f in feedbacks)
        return round(total / len(feedbacks), 1)

    def feedback_count(self):
        return self.feedbacks.count()


class Officer(UserMixin, db.Model):
    __tablename__ = 'officers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    badge_number = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    role = db.Column(db.Enum('admin', 'officer'), default='officer')
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'))
    phone = db.Column(db.String(15))
    rank = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'), nullable=False)
    acknowledgment_id = db.Column(db.String(50), unique=True, nullable=False)
    citizen_name = db.Column(db.String(200))
    mobile = db.Column(db.String(15))
    gender = db.Column(db.Enum('male', 'female', 'other', 'prefer_not_to_say'))
    age_group = db.Column(db.Enum('under_18', '18_25', '26_35', '36_45', '46_60', 'above_60'))
    behavior_rating = db.Column(db.Integer)
    response_rating = db.Column(db.Integer)
    cleanliness_rating = db.Column(db.Integer)
    helpfulness_rating = db.Column(db.Integer)
    transparency_rating = db.Column(db.Integer)
    overall_rating = db.Column(db.Integer)
    feedback_text = db.Column(db.Text)
    complaint = db.Column(db.Text)
    complaint_category = db.Column(db.Enum('corruption', 'misconduct', 'delay', 'rude_behavior', 'other'))
    sentiment = db.Column(db.Enum('positive', 'neutral', 'negative'))
    sentiment_score = db.Column(db.Float)
    image_path = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('officers.id'))
    resolved_at = db.Column(db.DateTime)
    resolution_note = db.Column(db.Text)
    is_flagged = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_ack_id():
        chars = string.ascii_uppercase + string.digits
        return 'GPF-' + ''.join(random.choices(chars, k=8))

    def avg_score(self):
        ratings = [self.behavior_rating, self.response_rating, self.cleanliness_rating,
                   self.helpfulness_rating, self.transparency_rating]
        valid = [r for r in ratings if r is not None]
        return round(sum(valid) / len(valid), 1) if valid else 0

    def analyze_sentiment(self):
        """Simple keyword-based sentiment analysis"""
        positive_words = ['excellent', 'good', 'great', 'helpful', 'polite', 'fast', 
                         'professional', 'satisfied', 'happy', 'best', 'amazing', 
                         'wonderful', 'efficient', 'cooperative', 'honest']
        negative_words = ['bad', 'rude', 'slow', 'corrupt', 'unhelpful', 'terrible',
                         'worst', 'poor', 'awful', 'disgusting', 'harass', 'bribe',
                         'delay', 'arrogant', 'negligent']
        
        text = ((self.feedback_text or '') + ' ' + (self.complaint or '')).lower()
        
        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        
        if self.overall_rating:
            if self.overall_rating >= 4:
                pos_count += 2
            elif self.overall_rating <= 2:
                neg_count += 2
        
        if pos_count > neg_count:
            self.sentiment = 'positive'
            self.sentiment_score = min(1.0, pos_count / (pos_count + neg_count + 1))
        elif neg_count > pos_count:
            self.sentiment = 'negative'
            self.sentiment_score = -min(1.0, neg_count / (pos_count + neg_count + 1))
        else:
            self.sentiment = 'neutral'
            self.sentiment_score = 0.0


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('feedback', 'complaint', 'system'), default='feedback')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    action = db.Column(db.String(200))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
