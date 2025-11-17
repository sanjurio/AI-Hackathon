import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
from models import db, User, Ticket, Category, TeamMember, Approval, TicketHistory
from ai_classifier import classify_ticket
from ticket_assignment import assign_ticket_to_team_member
from email_service import mail, send_approval_email, send_assignment_email
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

database_url = os.getenv('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketing.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@ticketing.com')

db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.must_change_password:
                flash('You must change your password on first login.', 'warning')
                return redirect(url_for('change_password'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
        else:
            current_user.password = generate_password_hash(new_password)
            current_user.must_change_password = False
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    tickets = Ticket.query.filter_by(created_by=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('user_dashboard.html', tickets=tickets)

@app.route('/user/create-ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        description = request.form.get('description')
        
        if not description or len(description) < 10:
            flash('Please provide a detailed description (at least 10 characters).', 'danger')
            return redirect(url_for('create_ticket'))
        
        category = classify_ticket(description)
        
        ticket = Ticket(
            description=description,
            category_id=category.id if category else None,
            created_by=current_user.id,
            status='Pending Approval'
        )
        db.session.add(ticket)
        db.session.commit()
        
        history = TicketHistory(
            ticket_id=ticket.id,
            action='Ticket Created',
            details=f'Category auto-classified as: {category.name if category else "Uncategorized"}'
        )
        db.session.add(history)
        db.session.commit()
        
        if category and category.approvers:
            ticket_id = ticket.id
            description = ticket.description
            category_name = category.name if category else 'Uncategorized'
            creator_name = current_user.name
            
            approvers = category.approvers.split(',')
            approval_ids = []
            for approver_email in approvers:
                approval = Approval(
                    ticket_id=ticket_id,
                    approver_email=approver_email.strip(),
                    status='Pending'
                )
                db.session.add(approval)
                approval_ids.append((approver_email.strip(), approval))
            db.session.commit()
            
            for approver_email, approval in approval_ids:
                token = serializer.dumps({'approval_id': approval.id, 'ticket_id': ticket_id}, salt='approval-token')
                send_approval_email(
                    ticket_id=ticket_id,
                    description=description,
                    category_name=category_name,
                    creator_name=creator_name,
                    approval_token=token,
                    approver_email=approver_email
                )
        
        flash('Ticket created successfully! Waiting for approval.', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('create_ticket.html')

@app.route('/user/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if not current_user.is_admin and ticket.created_by != current_user.id:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    history = TicketHistory.query.filter_by(ticket_id=ticket_id).order_by(TicketHistory.timestamp.desc()).all()
    approvals = Approval.query.filter_by(ticket_id=ticket_id).all()
    
    return render_template('view_ticket.html', ticket=ticket, history=history, approvals=approvals)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    total_tickets = Ticket.query.count()
    pending_tickets = Ticket.query.filter_by(status='Pending Approval').count()
    active_tickets = Ticket.query.filter(Ticket.status.in_(['Approved', 'Assigned', 'In Progress'])).count()
    completed_tickets = Ticket.query.filter_by(status='Completed').count()
    
    recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         total_tickets=total_tickets,
                         pending_tickets=pending_tickets,
                         active_tickets=active_tickets,
                         completed_tickets=completed_tickets,
                         recent_tickets=recent_tickets)

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        is_admin = request.form.get('is_admin') == 'on'
        dummy_password = request.form.get('password', 'Password123!')
        
        if User.query.filter_by(email=email).first():
            flash('User with this email already exists.', 'danger')
        else:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(dummy_password),
                is_admin=is_admin,
                must_change_password=True
            )
            db.session.add(user)
            db.session.commit()
            flash(f'User {name} created successfully with password: {dummy_password}', 'success')
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        keywords = request.form.get('keywords')
        approvers = request.form.get('approvers')
        
        category = Category(
            name=name,
            description=description,
            keywords=keywords,
            approvers=approvers
        )
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('manage_categories'))
    
    categories = Category.query.all()
    return render_template('manage_categories.html', categories=categories)

@app.route('/admin/team-members', methods=['GET', 'POST'])
@login_required
def manage_team_members():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        category_id = request.form.get('category_id')
        
        team_member = TeamMember(
            name=name,
            email=email,
            category_id=int(category_id)
        )
        db.session.add(team_member)
        db.session.commit()
        flash(f'Team member "{name}" added successfully!', 'success')
        return redirect(url_for('manage_team_members'))
    
    categories = Category.query.all()
    team_members = TeamMember.query.all()
    return render_template('manage_team_members.html', categories=categories, team_members=team_members)

@app.route('/admin/tickets')
@login_required
def admin_tickets():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(status=status_filter).order_by(Ticket.created_at.desc()).all()
    
    return render_template('admin_tickets.html', tickets=tickets, status_filter=status_filter)

@app.route('/approve/<token>/<action>')
def approve_ticket(token, action):
    try:
        data = serializer.loads(token, salt='approval-token', max_age=604800)
        approval_id = data.get('approval_id')
        ticket_id = data.get('ticket_id')
    except SignatureExpired:
        return render_template('approval_result.html', 
                             message='This approval link has expired (valid for 7 days).',
                             ticket=None), 400
    except BadSignature:
        return render_template('approval_result.html', 
                             message='Invalid approval link.',
                             ticket=None), 400
    
    approval = Approval.query.get_or_404(approval_id)
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if approval.ticket_id != ticket_id:
        return render_template('approval_result.html', 
                             message='Invalid approval link. This approval does not belong to this ticket.',
                             ticket=None), 400
    
    if approval.status != 'Pending':
        return render_template('approval_result.html',
                             message=f'This approval has already been {approval.status.lower()}.',
                             ticket=ticket)
    
    if action == 'approve':
        approval.status = 'Approved'
        approval.approved_at = datetime.utcnow()
        
        history = TicketHistory(
            ticket_id=ticket_id,
            action='Approval Received',
            details=f'Approved by {approval.approver_email}'
        )
        db.session.add(history)
        
        all_approvals = Approval.query.filter_by(ticket_id=ticket_id).all()
        if all(a.status == 'Approved' for a in all_approvals):
            ticket.status = 'Approved'
            
            assigned_member = assign_ticket_to_team_member(ticket)
            if assigned_member:
                ticket.assigned_to = assigned_member.id
                ticket.status = 'Assigned'
                
                history = TicketHistory(
                    ticket_id=ticket_id,
                    action='Ticket Assigned',
                    details=f'Assigned to {assigned_member.name}'
                )
                db.session.add(history)
                db.session.commit()
                
                send_assignment_email(
                    ticket_id=ticket.id,
                    description=ticket.description,
                    category_name=ticket.category.name if ticket.category else 'Uncategorized',
                    creator_name=ticket.creator.name,
                    team_member_name=assigned_member.name,
                    team_member_email=assigned_member.email
                )
        
        db.session.commit()
        message = 'Ticket approved successfully!'
    
    elif action == 'reject':
        approval.status = 'Rejected'
        approval.approved_at = datetime.utcnow()
        ticket.status = 'Rejected'
        
        history = TicketHistory(
            ticket_id=ticket_id,
            action='Ticket Rejected',
            details=f'Rejected by {approval.approver_email}'
        )
        db.session.add(history)
        db.session.commit()
        message = 'Ticket rejected.'
    
    else:
        message = 'Invalid action.'
    
    return render_template('approval_result.html', message=message, ticket=ticket)

@app.route('/api/ticket/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    new_status = request.json.get('status')
    
    if new_status in ['In Progress', 'Completed', 'Cancelled']:
        old_status = ticket.status
        ticket.status = new_status
        
        history = TicketHistory(
            ticket_id=ticket_id,
            action='Status Changed',
            details=f'Status changed from {old_status} to {new_status}'
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({'success': True, 'status': new_status})
    
    return jsonify({'error': 'Invalid status'}), 400

@app.cli.command()
def init_db():
    db.create_all()
    
    admin = User.query.filter_by(email='admin@company.com').first()
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@company.com',
            password=generate_password_hash('admin123'),
            is_admin=True,
            must_change_password=False
        )
        db.session.add(admin)
        db.session.commit()
        print('Database initialized! Admin user created: admin@company.com / admin123')
    else:
        print('Database already initialized.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
