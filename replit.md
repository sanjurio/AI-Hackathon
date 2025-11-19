# AI-Powered Ticketing System

## Project Overview

An intelligent ticketing system that automatically classifies and assigns support tickets using AI, eliminating the need for manual category selection. Built with Flask, PostgreSQL/SQLite, and OpenAI.

## Recent Changes

**November 19, 2025 - Email Service Migration to Resend**
- Migrated email service from Flask-Mail to Resend API for reliable transactional emails
- Updated all dummy @company.com email addresses to real Gmail accounts for testing
- Implemented auto-initialization system that seeds database on first startup
- Removed Flask-Mail dependency and cleaned up requirements.txt
- Configured Resend integration via Replit Connectors for secure API key management
- All approval and assignment emails now sent via Resend with HTML formatting

**November 17, 2025 - Phase 3: AI Integration and Admin Improvements**
- Integrated OpenAI API for intelligent ticket classification using GPT-3.5-turbo
- Added AI classification status badges (shows "AI Classified" vs "Keyword Classified")
- Created test mode for approvals - displays approval URLs when email is not configured
- Enhanced category management UI to support hierarchical approver configuration
- Updated approval hierarchy format: email:Role:Name | email:Role:Name
- Fixed AI classification tracking to reflect most recent classification (including edits)
- Improved admin experience with better approver hierarchy visualization

**November 17, 2025 - Phase 2: Multi-Layer Hierarchical Approval System**
- Enhanced approval model to support multi-layer hierarchical approval with levels, roles, and names
- Implemented sequential approval workflow (Level 1 → Level 2 → Level 3 → Level 4)
- Added edit ticket functionality (only allowed before approvals start)
- Added cancel ticket functionality (only allowed before approvals start)
- Enforced level-order approval (prevents out-of-order approvals)
- Updated UI to display hierarchical approval status with badges and detailed information
- Created comprehensive seed data script with realistic corporate approval hierarchies
- Fixed all critical issues identified in code review

**November 17, 2025 - Phase 1: Initial Setup**
- Initial project setup with complete AI ticketing system
- Implemented dual database support (PostgreSQL for Replit, SQLite for localhost)
- Created AI-powered ticket classification with OpenAI and fallback to native Python
- Built smart workload distribution algorithm for ticket assignment
- Implemented email approval workflow
- Created admin and user dashboards with modern Bootstrap UI
- Added comprehensive localhost deployment guide

## User Preferences

- **Database**: Dual support - PostgreSQL (production/Replit) and SQLite (local development)
- **Python Version**: Python 3.11+ 
- **AI Provider**: OpenAI with fallback to scikit-learn text classification
- **UI Framework**: Bootstrap 5 with custom CSS
- **Deployment**: Replit + localhost capability

## Project Architecture

### Backend Structure
```
Flask Application (app.py)
├── Authentication (Flask-Login)
├── Database Models (SQLAlchemy ORM)
├── AI Classification (ai_classifier.py)
│   ├── OpenAI GPT-3.5-turbo (primary)
│   └── TF-IDF + Keyword matching (fallback)
├── Smart Assignment (ticket_assignment.py)
└── Email Service (Resend API)
```

### Database Models
- **Users**: Authentication, admin roles, password management
- **Categories**: Ticket categories with keywords and hierarchical approvers
- **TeamMembers**: Support staff assigned to categories
- **Tickets**: Support requests with AI classification and editable before approval
- **Approvals**: Multi-layer hierarchical approval workflow with levels, roles, and sequential progression
- **TicketHistory**: Complete audit trail with edit/cancel tracking

### Key Features

1. **AI-Powered Classification**
   - Primary: OpenAI API for intelligent categorization
   - Fallback: Keyword matching + TF-IDF vectorization
   - No manual category selection required by users

2. **Smart Assignment Algorithm**
   - Evenly distributes tickets based on current workload
   - Example: 11 tickets, 5 team members
     - Tickets 1-5: Each member gets 1 (total: 1 each)
     - Tickets 6-10: Each member gets 1 more (total: 2 each)
     - Ticket 11: Goes to member with lowest count (back to 1)
   - Future: Will integrate out-of-office detection

3. **Authentication System**
   - Admin creates users with dummy passwords
   - Mandatory password change on first login
   - Role-based access (Admin vs User)
   - Session management with Flask-Login

4. **Multi-Layer Hierarchical Approval Workflow**
   - Sequential hierarchical approval (Level 1 → Level 2 → Level 3 → Level 4)
   - Email-based approval system with signed tokens
   - Each approval level has a role (Team Lead, Manager, Director, CFO, etc.)
   - Only current level receives approval notification
   - Next level automatically notified when current level approves
   - Level-order enforcement prevents out-of-order approvals
   - All levels must approve sequentially before assignment
   - Example: Hardware Request requires 4 levels:
     1. Team Lead (Level 1) - approves first
     2. Procurement Manager (Level 2) - notified after Level 1 approves
     3. Finance Director (Level 3) - notified after Level 2 approves
     4. CFO (Level 4) - notified after Level 3 approves
     5. Ticket auto-assigned after Level 4 approves

5. **User Experience**
   - Users see only their tickets and history
   - **Edit Tickets**: Users can edit ticket description before any approvals (auto-reclassifies)
   - **Cancel Tickets**: Users can cancel tickets before any approvals start
   - Admins see all tickets with filtering
   - Clean, modern Bootstrap interface with approval hierarchy visualization
   - Real-time status tracking with level badges
   - Clear indicators showing current approval status and next steps

### Environment Configuration

**Replit (Production)**
```
DATABASE_URL=<auto-provided-postgresql>
SESSION_SECRET=<auto-generated>
OPENAI_API_KEY=<user-provided>
RESEND_API_KEY=<configured-via-resend-integration>
RESEND_FROM_EMAIL=<configured-via-resend-integration>
```

**Localhost (Development)**
```
# SQLite used when DATABASE_URL is not set
SESSION_SECRET=<user-defines>
OPENAI_API_KEY=<optional>
MAIL_* settings (optional)
```

### File Organization

```
/
├── app.py                    # Main Flask app with routes + edit/cancel
├── models.py                 # SQLAlchemy database models with hierarchical approvals
├── ai_classifier.py          # AI classification logic
├── ticket_assignment.py      # Workload distribution algorithm
├── email_service.py          # Email notification service
├── seed_data.py             # Dummy data script with multi-layer approvals
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .gitignore               # Git exclusions
├── README.md                # Full documentation
├── LOCALHOST_SETUP.md       # Local deployment guide
├── templates/               # Jinja2 HTML templates
│   ├── base.html            # Base template with navbar
│   ├── login.html           # Login page
│   ├── change_password.html # Password change form
│   ├── user_dashboard.html  # User ticket view
│   ├── create_ticket.html   # Ticket creation form
│   ├── view_ticket.html     # Ticket details
│   ├── admin_dashboard.html # Admin overview
│   ├── admin_tickets.html   # All tickets view
│   ├── manage_users.html    # User management
│   ├── manage_categories.html # Category management
│   ├── manage_team_members.html # Team member management
│   └── approval_result.html # Approval confirmation
└── static/
    ├── css/style.css        # Custom styles
    └── js/main.js          # JavaScript utilities
```

### Technology Stack

**Backend:**
- Flask 3.1.2 (web framework)
- SQLAlchemy 2.0.44 (ORM)
- PostgreSQL / SQLite (databases)
- Flask-Login (authentication)
- Resend (email notifications)
- Werkzeug (password hashing)

**AI/ML:**
- OpenAI API (GPT-3.5-turbo)
- scikit-learn (TF-IDF, cosine similarity)
- pandas (data handling)

**Frontend:**
- Bootstrap 5 (UI framework)
- Bootstrap Icons
- Vanilla JavaScript
- Custom CSS

### Default Credentials

- **Admin Email**: thbsaitest1@gmail.com
- **Admin Password**: admin123
- **Note**: Admin user is auto-created on database initialization

### Workflow Configuration

- **Name**: flask-app
- **Command**: `python app.py`
- **Port**: 5000
- **Output Type**: webview (web preview)
- **Auto-restart**: Yes (on code changes)

### API Integration Status

- **OpenAI**: Configured via `OPENAI_API_KEY` (optional)
- **Email**: Configured via Resend integration (`RESEND_API_KEY` and `RESEND_FROM_EMAIL`)
- **Database**: Auto-configured (PostgreSQL on Replit, SQLite locally)

### Future Enhancements (Phase 2)

1. **Microsoft Teams Integration**
   - Check employee leave/availability status via Teams API
   - Auto-exclude unavailable team members from assignment

2. **Email Out-of-Office Detection**
   - Parse out-of-office auto-replies
   - Update team member availability automatically

3. **Chatbot Interface**
   - Conversational ticket creation
   - Status queries via chat
   - Natural language ticket updates

4. **Advanced Features**
   - SLA tracking and automated escalations
   - Priority levels for tickets
   - Analytics dashboard with metrics
   - Mobile Progressive Web App (PWA)
   - Custom notification preferences

### Known Limitations

- Teams/Outlook integration requires Microsoft Graph API setup (Phase 2)
- AI classification quality depends on category keywords and OpenAI API availability

### Development Notes

- **LSP Warnings**: Minor type checking warnings exist but don't affect functionality
- **Database Migration**: Uses direct table creation (not Alembic) for simplicity
- **Cache Control**: Recommended for production to prevent browser caching issues
- **Debug Mode**: Enabled by default in `app.py`, disable for production

### Testing the System

1. Login as admin (`thbsaitest1@gmail.com` / `admin123`)
2. Create categories with keywords and approvers
3. Add team members to categories
4. Create regular users
5. Login as user and create a ticket with natural language description
6. AI will classify and route to approvers
7. Approve via email or admin panel
8. System auto-assigns to least-loaded team member

### Security Considerations

- Passwords hashed with Werkzeug's pbkdf2:sha256
- Session management via Flask-Login
- CSRF protection via Flask
- SQL injection prevention via SQLAlchemy ORM
- Environment variables for sensitive data
- `.gitignore` configured to exclude secrets

### Deployment Options

**Replit (Current):**
- Automatic PostgreSQL provisioning
- Environment secrets management
- One-click deployment
- Auto-scaling capability

**Localhost:**
- See LOCALHOST_SETUP.md for complete guide
- SQLite for easy development
- Optional PostgreSQL for production testing
- Virtual environment isolation

**Production (Future):**
- Gunicorn WSGI server
- Nginx reverse proxy
- SSL/TLS certificates
- Production PostgreSQL database
- Redis for session storage (optional)

---

**Project Status**: ✅ Complete and functional
**Last Updated**: November 17, 2025
**Maintainer**: AI Agent (Replit)
