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
        
        print("\nCreating IT support team members (5 members)...")
        
        team_members_data = [
            {'name': 'Alice Support', 'email': 'thbsaitest6@gmail.com', 'password': 'support123', 'category': 'Software Installation'},
            {'name': 'Bob Support', 'email': 'thbsaitest7@gmail.com', 'password': 'support123', 'category': 'Software Installation'},
            {'name': 'Carol Support', 'email': 'thbsaitest8@gmail.com', 'password': 'support123', 'category': 'Hardware Request'},
            {'name': 'David Support', 'email': 'thbsaitest9@gmail.com', 'password': 'support123', 'category': 'Access Request'},
            {'name': 'Eve Support', 'email': 'thbsaitest10@gmail.com', 'password': 'support123', 'category': 'Software Installation'},
        ]
        
        team_members = {}
        for tm_data in team_members_data:
            user = User(
                name=tm_data['name'],
                email=tm_data['email'],
                password=generate_password_hash(tm_data['password']),
                is_admin=False,
                must_change_password=False
            )
            db.session.add(user)
            db.session.commit()
            
            team_member = TeamMember(
                name=tm_data['name'],
                email=tm_data['email'],
                category_id=categories[tm_data['category']].id
            )
            db.session.add(team_member)
            team_members[tm_data['email']] = team_member
            print(f"Created team member: {tm_data['name']} - {tm_data['email']} / {tm_data['password']} ({tm_data['category']})")
        
        db.session.commit()
        
        print("\nCreating 11 dummy tickets to demonstrate load balancing...")
        
        dummy_tickets_data = [
            {"description": "I need Microsoft Office installed on my laptop for presentation work", "category": "Software Installation"},
            {"description": "Can you install Adobe Photoshop on my computer?", "category": "Software Installation"},
            {"description": "I need a new laptop - current one is too slow for development", "category": "Hardware Request"},
            {"description": "Please provide me with a second monitor for productivity", "category": "Hardware Request"},
            {"description": "I need access to the finance database for reporting", "category": "Access Request"},
            {"description": "Can I get permissions to the HR portal?", "category": "Access Request"},
            {"description": "I need to install Slack on my work computer", "category": "Software Installation"},
            {"description": "My keyboard is broken, need a replacement", "category": "Hardware Request"},
            {"description": "I need access to the project management tool", "category": "Access Request"},
            {"description": "Can you install Python and VS Code on my machine?", "category": "Software Installation"},
            {"description": "I need a new mouse, the current one is not working", "category": "Hardware Request"}
        ]
        
        john = users['thbsaitest2@gmail.com']
        
        for idx, ticket_data in enumerate(dummy_tickets_data, 1):
            description = ticket_data["description"]
            category_name = ticket_data["category"]
            category = categories[category_name]
            
            ticket = Ticket(
                description=description,
                category_id=category.id if category else None,
                created_by=john.id,
                status='Pending Approval'
            )
            db.session.add(ticket)
            db.session.commit()
            
            history = TicketHistory(
                ticket_id=ticket.id,
                action='Ticket Created',
                details=f'Category assigned as: {category.name} (seed data for load balancing demonstration)'
            )
            db.session.add(history)
            db.session.commit()
            
            if category and category.approvers:
                approvers_data = category.approvers.split('|')
                
                for level_idx, approver_info in enumerate(approvers_data, start=1):
                    parts = approver_info.strip().split(':')
                    approver_email = parts[0].strip()
                    approver_role = parts[1].strip() if len(parts) > 1 else 'Approver'
                    approver_name = parts[2].strip() if len(parts) > 2 else ''
                    
                    approval = Approval(
                        ticket_id=ticket.id,
                        approver_email=approver_email,
                        approver_name=approver_name,
                        approver_role=approver_role,
                        approval_level=level_idx,
                        status='Approved',
                        approved_at=datetime.utcnow()
                    )
                    db.session.add(approval)
                
                db.session.commit()
                
                from ticket_assignment import assign_ticket_to_team_member
                assigned_member = assign_ticket_to_team_member(ticket)
                
                if assigned_member:
                    ticket.assigned_to = assigned_member.id
                    ticket.status = 'Assigned'
                    
                    history = TicketHistory(
                        ticket_id=ticket.id,
                        action='Ticket Assigned',
                        details=f'Assigned to {assigned_member.name}'
                    )
                    db.session.add(history)
                    db.session.commit()
                    
                    print(f"Ticket #{ticket.id}: '{description[:50]}...' → {category.name} → Assigned to {assigned_member.name}")
                else:
                    print(f"Ticket #{ticket.id}: '{description[:50]}...' → {category.name} → No team member available")
        
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
        
        print("\nIT SUPPORT TEAM MEMBERS (can view and work on assigned tickets):")
        print("-" * 60)
        for tm_data in team_members_data:
            print(f"  Email: {tm_data['email']:<40} Password: {tm_data['password']}")
            print(f"    Name: {tm_data['name']:<40} Category: {tm_data['category']}")
            print()
        
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
