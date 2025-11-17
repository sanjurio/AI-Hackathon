from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    must_change_password = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tickets = db.relationship('Ticket', backref='creator', lazy=True, foreign_keys='Ticket.created_by')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)
    approvers = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tickets = db.relationship('Ticket', backref='category', lazy=True)
    team_members = db.relationship('TeamMember', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assigned_tickets = db.relationship('Ticket', backref='assignee', lazy=True, foreign_keys='Ticket.assigned_to')
    
    def __repr__(self):
        return f'<TeamMember {self.name}>'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('team_members.id'))
    status = db.Column(db.String(50), default='Pending Approval')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    approvals = db.relationship('Approval', backref='ticket', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('TicketHistory', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Ticket {self.id} - {self.status}>'

class Approval(db.Model):
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    approver_email = db.Column(db.String(120), nullable=False)
    approver_name = db.Column(db.String(100))
    approver_role = db.Column(db.String(100))
    approval_level = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='Pending')
    approved_at = db.Column(db.DateTime)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Approval {self.id} - Level {self.approval_level} - {self.status}>'

class TicketHistory(db.Model):
    __tablename__ = 'ticket_history'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TicketHistory {self.id} - {self.action}>'
