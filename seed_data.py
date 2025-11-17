from app import app, db
from models import User, Category, TeamMember, Ticket, Approval, TicketHistory
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_database():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Clearing existing data...")
        TicketHistory.query.delete()
        Approval.query.delete()
        Ticket.query.delete()
        TeamMember.query.delete()
        Category.query.delete()
        User.query.delete()
        db.session.commit()
        
        print("Creating users...")
        
        users_data = [
            {'name': 'Admin User', 'email': 'admin@company.com', 'password': 'admin123', 'is_admin': True},
            {'name': 'John Employee', 'email': 'john.employee@company.com', 'password': 'password123', 'is_admin': False},
            {'name': 'Sarah Employee', 'email': 'sarah.employee@company.com', 'password': 'password123', 'is_admin': False},
            {'name': 'Mike Employee', 'email': 'mike.employee@company.com', 'password': 'password123', 'is_admin': False},
        ]
        
        users = {}
        for user_data in users_data:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                password=generate_password_hash(user_data['password']),
                is_admin=user_data['is_admin'],
                must_change_password=False
            )
            db.session.add(user)
            users[user_data['email']] = user
            print(f"Created user: {user.email} / {user_data['password']}")
        
        db.session.commit()
        
        print("\nCreating categories with hierarchical approvers...")
        
        categories_data = [
            {
                'name': 'Software Installation',
                'description': 'Software installation and licensing requests',
                'keywords': 'install, software, application, program, license, teams, zoom, office, adobe',
                'approvers': 'team.lead@company.com:Team Lead:Robert Johnson | it.manager@company.com:IT Manager:Emily Davis | it.director@company.com:IT Director:Michael Chen'
            },
            {
                'name': 'Timesheet Modification',
                'description': 'Timesheet corrections and modifications',
                'keywords': 'timesheet, hours, attendance, time, correction, modify, adjust',
                'approvers': 'supervisor@company.com:Supervisor:Lisa Anderson | hr.manager@company.com:HR Manager:David Wilson | hr.director@company.com:HR Director:Jennifer Martinez'
            },
            {
                'name': 'Hardware Request',
                'description': 'Hardware equipment requests (laptops, monitors, etc.)',
                'keywords': 'laptop, desktop, monitor, keyboard, mouse, hardware, equipment, device',
                'approvers': 'team.lead@company.com:Team Lead:Robert Johnson | procurement.manager@company.com:Procurement Manager:Amanda Taylor | finance.director@company.com:Finance Director:James Brown | cfo@company.com:CFO:Patricia White'
            },
            {
                'name': 'Access Request',
                'description': 'System and application access requests',
                'keywords': 'access, permission, credentials, login, account, rights, privileges',
                'approvers': 'team.lead@company.com:Team Lead:Robert Johnson | security.manager@company.com:Security Manager:Christopher Lee | it.director@company.com:IT Director:Michael Chen'
            },
            {
                'name': 'Travel Authorization',
                'description': 'Business travel and expense requests',
                'keywords': 'travel, trip, flight, hotel, expense, reimbursement, conference',
                'approvers': 'supervisor@company.com:Supervisor:Lisa Anderson | department.manager@company.com:Department Manager:Karen Rodriguez | finance.director@company.com:Finance Director:James Brown'
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category = Category(
                name=cat_data['name'],
                description=cat_data['description'],
                keywords=cat_data['keywords'],
                approvers=cat_data['approvers']
            )
            db.session.add(category)
            categories[cat_data['name']] = category
            
            approver_levels = cat_data['approvers'].split('|')
            print(f"\nCategory: {cat_data['name']}")
            print(f"  Approval hierarchy ({len(approver_levels)} levels):")
            for idx, approver in enumerate(approver_levels, 1):
                parts = approver.strip().split(':')
                email = parts[0].strip()
                role = parts[1].strip() if len(parts) > 1 else 'Approver'
                name = parts[2].strip() if len(parts) > 2 else email
                print(f"    Level {idx}: {name} ({role}) - {email}")
        
        db.session.commit()
        
        print("\nCreating team members...")
        
        team_members_data = [
            {'name': 'Alex Tech', 'email': 'alex.tech@company.com', 'category': 'Software Installation'},
            {'name': 'Bob Support', 'email': 'bob.support@company.com', 'category': 'Software Installation'},
            {'name': 'Carol HR', 'email': 'carol.hr@company.com', 'category': 'Timesheet Modification'},
            {'name': 'Dan IT', 'email': 'dan.it@company.com', 'category': 'Hardware Request'},
            {'name': 'Eve Security', 'email': 'eve.security@company.com', 'category': 'Access Request'},
        ]
        
        for tm_data in team_members_data:
            team_member = TeamMember(
                name=tm_data['name'],
                email=tm_data['email'],
                category_id=categories[tm_data['category']].id
            )
            db.session.add(team_member)
            print(f"Created team member: {tm_data['name']} ({tm_data['category']})")
        
        db.session.commit()
        
        print("\n" + "="*80)
        print("SEED DATA SUMMARY")
        print("="*80)
        print("\nREGULAR USERS (for creating tickets):")
        print("-" * 60)
        for user_data in users_data:
            if not user_data['is_admin']:
                print(f"  Email: {user_data['email']:<40} Password: {user_data['password']}")
        
        print("\nADMIN USER:")
        print("-" * 60)
        print(f"  Email: admin@company.com{' '*25} Password: admin123")
        
        print("\nAPPROVERS (receive approval emails):")
        print("-" * 60)
        print("  These email addresses will receive approval requests:")
        approvers_set = set()
        for cat_data in categories_data:
            for approver in cat_data['approvers'].split('|'):
                email = approver.strip().split(':')[0].strip()
                role = approver.strip().split(':')[1].strip() if ':' in approver else 'Approver'
                name = approver.strip().split(':')[2].strip() if approver.count(':') >= 2 else ''
                approvers_set.add(f"  {email:<45} ({role} - {name})")
        for approver in sorted(approvers_set):
            print(approver)
        
        print("\nCATEGORIES WITH APPROVAL HIERARCHY:")
        print("-" * 60)
        for cat_data in categories_data:
            print(f"\n{cat_data['name']}:")
            approver_levels = cat_data['approvers'].split('|')
            for idx, approver in enumerate(approver_levels, 1):
                parts = approver.strip().split(':')
                email = parts[0].strip()
                role = parts[1].strip() if len(parts) > 1 else 'Approver'
                name = parts[2].strip() if len(parts) > 2 else email
                print(f"  Level {idx}: {role} ({name})")
        
        print("\n" + "="*80)
        print("HOW TO TEST:")
        print("="*80)
        print("1. Login as: john.employee@company.com / password123")
        print("2. Create a ticket (e.g., 'I need Microsoft Office installed on my laptop')")
        print("3. The ticket will be auto-classified to 'Software Installation'")
        print("4. Check approval emails - ONLY Level 1 (Team Lead) gets notified first")
        print("5. When Level 1 approves, Level 2 (IT Manager) gets notified")
        print("6. When Level 2 approves, Level 3 (IT Director) gets notified")
        print("7. After ALL levels approve, the ticket is auto-assigned to a team member")
        print("8. You can EDIT or CANCEL the ticket ONLY before any approvals happen")
        print("="*80 + "\n")

if __name__ == '__main__':
    seed_database()
