import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
from models import db, User, Ticket, Category, TeamMember, Approval, TicketHistory
from ai_classifier import classify_ticket
from ticket_assignment import assign_ticket_to_team_member
from email_service import send_approval_email, send_assignment_email, init_mail
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')

init_mail(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

database_url = os.getenv('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketing.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20,
    'connect_args': {
        'connect_timeout': 10,
    }
}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def auto_initialize_database():
    """Automatically initialize and seed database if empty"""
    with app.app_context():
        try:
            db.create_all()
            
            if User.query.count() == 0:
                print("Database is empty. Auto-seeding...")
                from seed_data import seed_database
                seed_database()
                print("Database seeded successfully!")
        except Exception as e:
            print(f"Auto-initialization error: {e}")

auto_initialize_database()

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
    try:
        logout_user()
        flash('You have been logged out.', 'info')
    except Exception as e:
        app.logger.error(f"Logout error: {e}")
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
    
    team_member = TeamMember.query.filter_by(email=current_user.email).first()
    
    if team_member:
        return redirect(url_for('team_member_dashboard'))
    
    tickets = Ticket.query.filter_by(created_by=current_user.id).order_by(Ticket.created_at.desc()).all()
    
    pending_approvals = db.session.query(Ticket).join(Approval).filter(
        Approval.approver_email == current_user.email,
        Approval.status == 'Pending'
    ).order_by(Ticket.created_at.desc()).all()
    
    return render_template('user_dashboard.html', tickets=tickets, pending_approvals=pending_approvals)

@app.route('/team/dashboard')
@login_required
def team_member_dashboard():
    team_member = TeamMember.query.filter_by(email=current_user.email).first()
    
    if not team_member:
        flash('You are not registered as a team member.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    assigned_tickets = Ticket.query.filter_by(assigned_to=team_member.id).order_by(Ticket.created_at.desc()).all()
    
    active_tickets = [t for t in assigned_tickets if t.status in ['Assigned', 'In Progress']]
    completed_tickets = [t for t in assigned_tickets if t.status == 'Completed']
    
    return render_template('team_member_dashboard.html', 
                         team_member=team_member,
                         assigned_tickets=assigned_tickets,
                         active_tickets=active_tickets,
                         completed_tickets=completed_tickets)

@app.route('/user/create-ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        description = request.form.get('description')
        
        if not description or len(description) < 10:
            flash('Please provide a detailed description (at least 10 characters).', 'danger')
            return redirect(url_for('create_ticket'))
        
        category, ai_used = classify_ticket(description)
        
        ticket = Ticket(
            description=description,
            category_id=category.id if category else None,
            created_by=current_user.id,
            status='Pending Approval'
        )
        db.session.add(ticket)
        db.session.commit()
        
        classification_method = 'AI (OpenAI)' if ai_used else 'Keyword matching'
        history = TicketHistory(
            ticket_id=ticket.id,
            action='Ticket Created',
            details=f'Category auto-classified as: {category.name if category else "Uncategorized"} using {classification_method}'
        )
        db.session.add(history)
        db.session.commit()
        
        if category and category.approvers:
            ticket_id = ticket.id
            description = ticket.description
            category_name = category.name if category else 'Uncategorized'
            creator_name = current_user.name
            
            approvers_data = category.approvers.split('|')
            approval_ids = []
            for idx, approver_info in enumerate(approvers_data, start=1):
                parts = approver_info.strip().split(':')
                approver_email = parts[0].strip()
                approver_role = parts[1].strip() if len(parts) > 1 else 'Approver'
                approver_name = parts[2].strip() if len(parts) > 2 else ''
                
                approval = Approval(
                    ticket_id=ticket_id,
                    approver_email=approver_email,
                    approver_name=approver_name,
                    approver_role=approver_role,
                    approval_level=idx,
                    status='Pending' if idx == 1 else 'Waiting'
                )
                db.session.add(approval)
                approval_ids.append((approver_email, approver_role, approver_name, approval, idx))
            db.session.commit()
            
            for approver_email, approver_role, approver_name, approval, idx in approval_ids:
                if idx == 1:
                    token = serializer.dumps({'approval_id': approval.id, 'ticket_id': ticket_id}, salt='approval-token')
                    email_sent = send_approval_email(
                        ticket_id=ticket_id,
                        description=description,
                        category_name=category_name,
                        creator_name=creator_name,
                        approval_token=token,
                        approver_email=approver_email
                    )
                    if email_sent:
                        print(f"✓ Approval email sent to {approver_email} for ticket #{ticket_id}")
                    else:
                        print(f"✗ Failed to send approval email to {approver_email} for ticket #{ticket_id}")
        
        flash('Ticket created successfully! Waiting for approval.', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('create_ticket.html')

@app.route('/user/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    history = TicketHistory.query.filter_by(ticket_id=ticket_id).order_by(TicketHistory.timestamp.desc()).all()
    approvals = Approval.query.filter_by(ticket_id=ticket_id).order_by(Approval.approval_level).all()
    
    is_approver = any(a.approver_email == current_user.email for a in approvals)
    team_member = TeamMember.query.filter_by(email=current_user.email).first()
    is_assigned = team_member and ticket.assigned_to == team_member.id
    
    if not current_user.is_admin and ticket.created_by != current_user.id and not is_approver and not is_assigned:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    can_edit = (ticket.created_by == current_user.id and 
                ticket.status == 'Pending Approval' and 
                not any(a.status == 'Approved' for a in approvals))
    
    classification_history = [h for h in history if h.action in ['Ticket Created', 'Ticket Edited'] and h.details and 'using' in h.details]
    ai_classified = False
    if classification_history:
        latest_classification = classification_history[0]
        ai_classified = 'AI' in latest_classification.details or 'OpenAI' in latest_classification.details
    
    test_mode_urls = []
    from email_service import get_email_configured
    email_configured = get_email_configured()
    if not email_configured and approvals:
        for approval in approvals:
            token = serializer.dumps({'approval_id': approval.id, 'ticket_id': ticket_id}, salt='approval-token')
            test_mode_urls.append({
                'level': approval.approval_level,
                'role': approval.approver_role or 'Approver',
                'approve_url': url_for('approve_ticket', token=token, action='approve', _external=True),
                'reject_url': url_for('approve_ticket', token=token, action='reject', _external=True)
            })
    
    current_user_approval = next((a for a in approvals if a.approver_email == current_user.email and a.status == 'Pending'), None)
    approval_token = None
    if current_user_approval:
        approval_token = serializer.dumps({'approval_id': current_user_approval.id, 'ticket_id': ticket_id}, salt='approval-token')
    
    return render_template('view_ticket.html', 
                         ticket=ticket, 
                         history=history, 
                         approvals=approvals, 
                         can_edit=can_edit,
                         ai_classified=ai_classified,
                         test_mode_urls=test_mode_urls,
                         current_user_approval=current_user_approval,
                         approval_token=approval_token,
                         is_assigned=is_assigned,
                         team_member=team_member)

@app.route('/user/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.created_by != current_user.id:
        flash('You do not have permission to edit this ticket.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    approvals = Approval.query.filter_by(ticket_id=ticket_id).all()
    if ticket.status != 'Pending Approval' or any(a.status == 'Approved' for a in approvals):
        flash('Cannot edit ticket after approvals have started.', 'danger')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    if request.method == 'POST':
        new_description = request.form.get('description')
        
        if not new_description or len(new_description) < 10:
            flash('Please provide a detailed description (at least 10 characters).', 'danger')
            return redirect(url_for('edit_ticket', ticket_id=ticket_id))
        
        old_description = ticket.description
        ticket.description = new_description
        
        category, ai_used = classify_ticket(new_description)
        old_category = ticket.category
        ticket.category_id = category.id if category else None
        
        classification_method = 'AI (OpenAI)' if ai_used else 'Keyword matching'
        history = TicketHistory(
            ticket_id=ticket.id,
            action='Ticket Edited',
            details=f'Description updated. Category changed from {old_category.name if old_category else "None"} to {category.name if category else "None"} using {classification_method}'
        )
        db.session.add(history)
        
        Approval.query.filter_by(ticket_id=ticket_id).delete()
        
        if category and category.approvers:
            approvers_data = category.approvers.split('|')
            approval_list = []
            for idx, approver_info in enumerate(approvers_data, start=1):
                parts = approver_info.strip().split(':')
                approver_email = parts[0].strip()
                approver_role = parts[1].strip() if len(parts) > 1 else 'Approver'
                approver_name = parts[2].strip() if len(parts) > 2 else ''
                
                approval = Approval(
                    ticket_id=ticket_id,
                    approver_email=approver_email,
                    approver_name=approver_name,
                    approver_role=approver_role,
                    approval_level=idx,
                    status='Pending' if idx == 1 else 'Waiting'
                )
                db.session.add(approval)
                approval_list.append((approver_email, approval, idx))
            
            db.session.commit()
            
            for approver_email, approval, idx in approval_list:
                if idx == 1:
                    token = serializer.dumps({'approval_id': approval.id, 'ticket_id': ticket_id}, salt='approval-token')
                    send_approval_email(
                        ticket_id=ticket_id,
                        description=new_description,
                        category_name=category.name,
                        creator_name=current_user.name,
                        approval_token=token,
                        approver_email=approver_email
                    )
        else:
            db.session.commit()
        flash('Ticket updated successfully!', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    return render_template('create_ticket.html', ticket=ticket, is_edit=True)

@app.route('/user/ticket/<int:ticket_id>/cancel', methods=['POST'])
@login_required
def cancel_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.created_by != current_user.id:
        flash('You do not have permission to cancel this ticket.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    approvals = Approval.query.filter_by(ticket_id=ticket_id).all()
    if ticket.status != 'Pending Approval' or any(a.status == 'Approved' for a in approvals):
        flash('Cannot cancel ticket after approvals have started.', 'danger')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    ticket.status = 'Cancelled'
    
    for approval in approvals:
        if approval.status in ['Pending', 'Waiting']:
            approval.status = 'Cancelled'
    
    history = TicketHistory(
        ticket_id=ticket_id,
        action='Ticket Cancelled',
        details=f'Ticket cancelled by {current_user.name} before any approvals'
    )
    db.session.add(history)
    db.session.commit()
    
    flash('Ticket cancelled successfully.', 'info')
    return redirect(url_for('user_dashboard'))

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

@app.route('/approve/<token>/<action>', methods=['GET', 'POST'])
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
    
    if approval.status == 'Waiting':
        return render_template('approval_result.html',
                             message='This approval is not ready yet. A previous level must approve first.',
                             ticket=ticket), 400
    
    if approval.status != 'Pending':
        return render_template('approval_result.html',
                             message=f'This approval has already been {approval.status.lower()}.',
                             ticket=ticket)
    
    previous_level = approval.approval_level - 1
    if previous_level > 0:
        prev_approval = Approval.query.filter_by(
            ticket_id=ticket_id, 
            approval_level=previous_level
        ).first()
        if prev_approval and prev_approval.status != 'Approved':
            return render_template('approval_result.html',
                                 message=f'Cannot approve at Level {approval.approval_level}. Previous level must approve first.',
                                 ticket=ticket), 400
    
    if request.method == 'GET':
        return render_template('approval_form.html', 
                             ticket=ticket, 
                             approval=approval, 
                             action=action,
                             token=token)
    
    comment = request.form.get('comment', '').strip()
    
    if action == 'approve':
        approval.status = 'Approved'
        approval.approved_at = datetime.utcnow()
        approval.comments = comment if comment else None
        
        role_info = f" ({approval.approver_role})" if approval.approver_role else ""
        name_info = approval.approver_name if approval.approver_name else approval.approver_email
        
        comment_info = f" - Comment: {comment}" if comment else ""
        history = TicketHistory(
            ticket_id=ticket_id,
            action='Approval Received',
            details=f'Level {approval.approval_level} approved by {name_info}{role_info}{comment_info}'
        )
        db.session.add(history)
        
        all_approvals = Approval.query.filter_by(ticket_id=ticket_id).order_by(Approval.approval_level).all()
        
        next_level = approval.approval_level + 1
        next_approval = Approval.query.filter_by(ticket_id=ticket_id, approval_level=next_level).first()
        
        if next_approval and next_approval.status == 'Waiting':
            next_approval.status = 'Pending'
            db.session.commit()
            
            token = serializer.dumps({'approval_id': next_approval.id, 'ticket_id': ticket_id}, salt='approval-token')
            email_sent = send_approval_email(
                ticket_id=ticket_id,
                description=ticket.description,
                category_name=ticket.category.name if ticket.category else 'Uncategorized',
                creator_name=ticket.creator.name,
                approval_token=token,
                approver_email=next_approval.approver_email
            )
            if email_sent:
                print(f"✓ Next level approval email sent to {next_approval.approver_email} for ticket #{ticket_id}")
            else:
                print(f"✗ Failed to send next level approval email to {next_approval.approver_email}")
        
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
                
                email_sent = send_assignment_email(
                    ticket_id=ticket.id,
                    description=ticket.description,
                    category_name=ticket.category.name if ticket.category else 'Uncategorized',
                    creator_name=ticket.creator.name,
                    team_member_name=assigned_member.name,
                    team_member_email=assigned_member.email
                )
                if email_sent:
                    print(f"✓ Assignment email sent to {assigned_member.email} for ticket #{ticket.id}")
                else:
                    print(f"✗ Failed to send assignment email to {assigned_member.email}")
        
        db.session.commit()
        message = f'Ticket approved successfully at Level {approval.approval_level}!'
    
    elif action == 'reject':
        approval.status = 'Rejected'
        approval.approved_at = datetime.utcnow()
        approval.comments = comment if comment else None
        ticket.status = 'Rejected'
        
        role_info = f" ({approval.approver_role})" if approval.approver_role else ""
        name_info = approval.approver_name if approval.approver_name else approval.approver_email
        comment_info = f" - Reason: {comment}" if comment else ""
        
        history = TicketHistory(
            ticket_id=ticket_id,
            action='Ticket Rejected',
            details=f'Rejected by {name_info}{role_info}{comment_info}'
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
    ticket = Ticket.query.get_or_404(ticket_id)
    team_member = TeamMember.query.filter_by(email=current_user.email).first()
    
    if not current_user.is_admin and not (team_member and ticket.assigned_to == team_member.id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    new_status = request.json.get('status')
    resolution_comment = request.json.get('resolution_comment', '').strip()
    
    if new_status in ['In Progress', 'Completed', 'Cancelled']:
        old_status = ticket.status
        ticket.status = new_status
        
        if resolution_comment:
            ticket.resolution_comment = resolution_comment
        
        details = f'Status changed from {old_status} to {new_status}'
        if resolution_comment and new_status == 'Completed':
            details += f' - Resolution: {resolution_comment}'
        elif resolution_comment:
            details += f' - Note: {resolution_comment}'
        
        history = TicketHistory(
            ticket_id=ticket_id,
            action='Status Changed',
            details=details
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
