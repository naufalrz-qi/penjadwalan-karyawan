from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class Branch(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), nullable=False)
    
    # Relationships
    jobdesks = db.relationship('Jobdesk', backref='branch', lazy=True, cascade='all, delete-orphan')
    employees = db.relationship('Employee', backref='branch', lazy=True, cascade='all, delete-orphan')
    schedules = db.relationship('SchedulePeriod', backref='branch', lazy=True, cascade='all, delete-orphan')

class Jobdesk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.String(36), db.ForeignKey('branch.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)

class Employee(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(1), nullable=False) # 'P' or 'W'
    branch_id = db.Column(db.String(36), db.ForeignKey('branch.id'), nullable=False)
    jobdesk_name = db.Column(db.String(50), nullable=False)
    
    # Relationship
    shifts = db.relationship('DailyShift', backref='employee', lazy=True, cascade='all, delete-orphan')

class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.JSON, nullable=False)

class SchedulePeriod(db.Model):
    period_key = db.Column(db.String(50), primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    branch_id = db.Column(db.String(36), db.ForeignKey('branch.id'), nullable=True) # Empty allowed for "Semua Cabang"
    label = db.Column(db.String(50), nullable=False)
    generated = db.Column(db.Boolean, default=False)
    
    shifts = db.relationship('DailyShift', backref='period', lazy=True, cascade='all, delete-orphan')

class DailyShift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_key = db.Column(db.String(50), db.ForeignKey('schedule_period.period_key'), nullable=False)
    employee_id = db.Column(db.String(36), db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False) # Format: YYYY-MM-DD
    status = db.Column(db.String(10), nullable=False) # PAGI, SIANG, OFF, CUTI
