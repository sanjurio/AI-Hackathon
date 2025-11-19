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
            {'name': 'Admin User', 'email': 'thbsaitest1@gmail.com', 'password': 'admin123', 'is_admin': True},
            {'name': 'John Employee', 'email': 'thbsaitest2@gmail.com', 'password': 'password123', 'is_admin': False},
            {'name': 'Sarah Employee', 'email': 'thbsaitest3@gmail.com', 'password': 'password123', 'is_admin': False},
            {'name': 'Mike Employee', 'email': 'thbsaitest5@gmail.com', 'password': 'password123', 'is_admin': False},
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
                'approvers': 'thbsaitest3@gmail.com:Team Lead:Sarah Employee | thbsaitest5@gmail.com:IT Manager:Mike Employee'
            },
            {
                'name': 'Timesheet Modification',
                'description': 'Timesheet corrections and modifications',
                'keywords': 'timesheet, hours, attendance, time, correction, modify, adjust',
                'approvers': 'thbsaitest6@gmail.com:Supervisor:Support Team | thbsaitest3@gmail.com:HR Manager:Sarah Employee'
            },
            {
                'name': 'Hardware Request',
                'description': 'Hardware equipment requests (laptops, monitors, etc.)',
                'keywords': 'laptop, desktop, monitor, keyboard, mouse, hardware, equipment, device',
                'approvers': 'thbsaitest5@gmail.com:Team Lead:Mike Employee | thbsaitest6@gmail.com:Procurement Manager:Support Team'
            },
            {
                'name': 'Access Request',
                'description': 'System and application access requests',
                'keywords': 'access, permission, credentials, login, account, rights, privileges',
                'approvers': 'thbsaitest3@gmail.com:Team Lead:Sarah Employee | thbsaitest5@gmail.com:Security Manager:Mike Employee'
            },
            {
                'name': 'Travel Authorization',
                'description': 'Business travel and expense requests',
                'keywords': 'travel, trip, flight, hotel, expense, reimbursement, conference',
                'approvers': 'thbsaitest6@gmail.com:Supervisor:Support Team | thbsaitest3@gmail.com:Manager:Sarah Employee'
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
            {'name': 'Tech Support', 'email': 'thbsaitest6@gmail.com', 'category': 'Software Installation'},
            {'name': 'HR Support', 'email': 'thbsaitest6@gmail.com', 'category': 'Timesheet Modification'},
            {'name': 'IT Support', 'email': 'thbsaitest6@gmail.com', 'category': 'Hardware Request'},
            {'name': 'Security Support', 'email': 'thbsaitest6@gmail.com', 'category': 'Access Request'},
            {'name': 'Travel Support', 'email': 'thbsaitest6@gmail.com', 'category': 'Travel Authorization'},
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
        print(f"  Email: thbsaitest1@gmail.com{' '*20} Password: admin123")
        
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
        print("1. Login as: thbsaitest2@gmail.com / password123")
        print("2. Create a ticket (e.g., 'I need Microsoft Office installed on my laptop')")
        print("3. The ticket will be auto-classified to 'Software Installation'")
        print("4. Check approval emails - ONLY Level 1 approver gets notified first")
        print("5. When Level 1 approves, Level 2 gets notified")
        print("6. After ALL levels approve, the ticket is auto-assigned to a team member")
        print("7. You can EDIT or CANCEL the ticket ONLY before any approvals happen")
        print("="*80 + "\n")

if __name__ == '__main__':
    seed_database()
