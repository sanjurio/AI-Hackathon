# AI-Powered Ticketing System

An intelligent ticketing system that uses AI to automatically classify and assign tickets without manual category selection.

## Features

- **AI-Powered Classification**: Automatically categorizes tickets using OpenAI with fallback to native Python text classification
- **Smart Ticket Assignment**: Evenly distributes workload among team members based on current ticket count
- **Multi-Level Approvals**: Email-based approval workflow before ticket assignment
- **User Management**: Admin-created accounts with mandatory password change on first login
- **Admin Dashboard**: Complete management interface for users, categories, and team members
- **Ticket Tracking**: Users can view their tickets and complete history
- **Email Notifications**: Automated emails for approvals and assignments
- **Dual Database Support**: PostgreSQL for production, SQLite for local development

## Tech Stack

- **Backend**: Python 3.11+ with Flask
- **Database**: PostgreSQL (production) / SQLite (local)
- **ORM**: SQLAlchemy
- **AI**: OpenAI API + scikit-learn
- **Frontend**: Bootstrap 5, HTML, CSS, JavaScript
- **Email**: Flask-Mail

## Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL (for production) or SQLite (for local)
- OpenAI API key (optional, falls back to keyword classification)

### Setup for Replit

1. The project is already configured for Replit with PostgreSQL
2. Set your OpenAI API key (optional):
   - The system will prompt you if needed
3. Run the application - it will auto-initialize the database

### Setup for Localhost

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ticketing-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   - For SQLite (local development):
     ```
     # Comment out or remove DATABASE_URL
     # DATABASE_URL=
     ```
   
   - For PostgreSQL (production):
     ```
     DATABASE_URL=postgresql://username:password@localhost/ticketing_db
     ```
   
   - OpenAI API Key (optional):
     ```
     OPENAI_API_KEY=sk-your-api-key-here
     ```
   
   - Email Configuration (optional):
     ```
     MAIL_SERVER=smtp.gmail.com
     MAIL_PORT=587
     MAIL_USE_TLS=True
     MAIL_USERNAME=your-email@gmail.com
     MAIL_PASSWORD=your-app-password
     MAIL_DEFAULT_SENDER=noreply@ticketing.com
     ```

5. **Initialize the database**
   ```bash
   flask init-db
   ```
   
   This creates:
   - All database tables
   - Default admin user: `admin@company.com` / `admin123`

6. **Run the application**
   ```bash
   python app.py
   ```
   
   The application will be available at: `http://localhost:5000`

## Usage

### First Time Setup

1. **Login as Admin**
   - Email: `admin@company.com`
   - Password: `admin123`

2. **Create Categories**
   - Go to Manage → Categories
   - Add categories like "Software Installation", "Timesheet Modification", "Hardware Request"
   - Add keywords for AI classification
   - Specify approver emails

3. **Add Team Members**
   - Go to Manage → Team Members
   - Add team members and assign them to categories
   - They will receive tickets from their assigned categories

4. **Create Users**
   - Go to Manage → Users
   - Create user accounts with dummy passwords
   - Users must change password on first login

### Creating Tickets

1. Login as a regular user
2. Click "New Ticket"
3. Describe your request in natural language
4. AI automatically classifies and routes the ticket
5. Approvers receive email notifications
6. After approval, ticket is auto-assigned to least-loaded team member

### Ticket Workflow

```
User Creates Ticket
    ↓
AI Classifies Category
    ↓
Sent to Approvers (Email)
    ↓
All Approvers Approve
    ↓
Auto-Assigned to Team Member (Smart Algorithm)
    ↓
Team Member Works on Ticket
    ↓
Ticket Completed
```

## Smart Assignment Algorithm

The system assigns tickets based on:
1. Team members assigned to the ticket's category
2. Current active ticket count per team member
3. Availability status

Example:
- 10 tickets to assign, 5 team members available
- First 5 tickets: each member gets 1 ticket
- Next 5 tickets: each member gets 1 more ticket (2 total)
- 11th ticket: goes to member with lowest count
- Future tickets skip members with more tickets

## Configuration

### Database Switching

The app automatically detects the database:
- If `DATABASE_URL` environment variable exists → Uses PostgreSQL
- If no `DATABASE_URL` → Uses SQLite (`ticketing.db`)

### AI Classification

The system uses two methods:
1. **OpenAI API** (if `OPENAI_API_KEY` is set)
2. **Fallback to keyword matching + TF-IDF** (if no API key)

Both methods work well, but OpenAI provides more accurate classification.

## Project Structure

```
ticketing-system/
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── ai_classifier.py            # AI classification logic
├── ticket_assignment.py        # Smart assignment algorithm
├── email_service.py            # Email notifications
├── templates/                  # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── user_dashboard.html
│   ├── admin_dashboard.html
│   └── ...
├── static/
│   ├── css/style.css          # Custom styles
│   └── js/main.js             # JavaScript
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## Future Enhancements (Phase 2)

- Microsoft Teams integration for leave status checking
- Out-of-office email detection
- Chatbot interface for ticket creation
- SLA tracking and automated escalations
- Analytics dashboard
- Mobile PWA support

## Troubleshooting

### Database Issues

**Problem**: Database not initializing
```bash
# Solution: Run init command
flask init-db
```

**Problem**: SQLite permission errors
```bash
# Solution: Check file permissions
chmod 644 ticketing.db
```

### Email Issues

**Problem**: Emails not sending
- Check MAIL_* environment variables
- For Gmail, use App Password (not regular password)
- Ensure "Less secure app access" is enabled (or use OAuth2)

### AI Classification Issues

**Problem**: Poor classification accuracy
- Add more keywords to categories
- Provide better category descriptions
- Consider adding OPENAI_API_KEY for better results

## License

MIT License - feel free to use for your organization!

## Support

For issues or questions, please contact your system administrator.
