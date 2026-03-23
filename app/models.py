from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farms = db.relationship('Farm', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Farm(db.Model):
    __tablename__ = 'farms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    village = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    chickens_batches = db.relationship('ChickenBatch', backref='farm', lazy=True, cascade='all, delete-orphan')
    feed_stocks = db.relationship('FeedStock', backref='farm', lazy=True, cascade='all, delete-orphan')
    feed_usages = db.relationship('FeedUsage', backref='farm', lazy=True, cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='farm', lazy=True, cascade='all, delete-orphan')


class ChickenBatch(db.Model):
    __tablename__ = 'chicken_batches'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    initial_count = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    daily_records = db.relationship('ChickenDaily', backref='batch', lazy=True, cascade='all, delete-orphan')


class ChickenDaily(db.Model):
    __tablename__ = 'chickens_daily'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('chicken_batches.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, default=0)
    sold_count = db.Column(db.Integer, default=0)
    remaining = db.Column(db.Integer, nullable=False)
    entry_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.String(200), nullable=True)


class FeedStock(db.Model):
    __tablename__ = 'feed_stock'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    bags_added = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FeedUsage(db.Model):
    __tablename__ = 'feed_usage'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    bags_used = db.Column(db.Float, default=0)
    entry_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.String(200), nullable=True)


class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    sale_code = db.Column(db.String(20), unique=True, nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft / completed
    sale_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = db.relationship('SaleEntry', backref='sale', lazy=True, cascade='all, delete-orphan')
    customer = db.relationship('Customer', backref='sale', uselist=False, cascade='all, delete-orphan')


class SaleEntry(db.Model):
    __tablename__ = 'sale_entries'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    entry_number = db.Column(db.Integer, nullable=False)
    empty_boxes = db.Column(db.Integer, default=0)
    empty_weight = db.Column(db.Float, default=0.0)
    chickens_per_box = db.Column(db.Integer, default=0)
    load_weight = db.Column(db.Float, default=0.0)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=True)
    price_per_kg = db.Column(db.Float, default=0.0)
