from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    address = db.Column(db.Text)
    role = db.Column(db.String(10), default='user')

class Jewel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(200))
    price_per_hour = db.Column(db.Float, default=0.0)
    fine_per_hour = db.Column(db.Float, default=0.0)
    count = db.Column(db.Integer, default=1)

class BorrowRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    jewel_id = db.Column(db.Integer, db.ForeignKey('jewel.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    calculated_amount = db.Column(db.Float, default=0.0)
    fine_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)

    user = db.relationship('User', backref='requests')
    jewel = db.relationship('Jewel', backref='requests')
