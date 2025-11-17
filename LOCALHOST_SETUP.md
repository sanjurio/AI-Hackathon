# Local Development Setup Guide

This guide will help you run the AI Ticketing System on your local machine (Windows, macOS, or Linux).

## Prerequisites

Before you begin, ensure you have:
- **Python 3.11 or higher** installed ([Download Python](https://www.python.org/downloads/))
- **Git** (optional, for cloning) ([Download Git](https://git-scm.com/downloads))
- **PostgreSQL** (optional, for production-like setup) ([Download PostgreSQL](https://www.postgresql.org/download/))

## Quick Start (Using SQLite)

For local development, the easiest way is to use SQLite:

### Step 1: Download the Project

If you have the project files:
```bash
cd ticketing-system
```

Or clone from Replit:
```bash
# Download the project ZIP from Replit and extract it
# Or use git if you've connected a repository
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install Flask, SQLAlchemy, OpenAI, and all other required packages.

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# On Windows (Command Prompt)
copy .env.example .env

# On macOS/Linux or Windows (PowerShell)
cp .env.example .env
```

Edit `.env` and update these settings:

**For SQLite (Local Development):**
```env
# Leave DATABASE_URL commented out or remove it to use SQLite
# DATABASE_URL=

# Session secret (change this!)
SESSION_SECRET=your-random-secret-key-here

# OpenAI API Key (optional - system works without it)
# Get your key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-api-key-here

# Email settings (optional - for testing approval emails)
# For Gmail, use an App Password, not your regular password
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password
# MAIL_DEFAULT_SENDER=noreply@ticketing.com
```

**Note:** 
- If `OPENAI_API_KEY` is not set, the system will use keyword-based classification (still works well!)
- If email settings are not configured, approval emails will be logged to console instead of sent

### Step 5: Initialize Database

```bash
flask init-db
```

You should see:
```
Database initialized! Admin user created: admin@company.com / admin123
```

This creates:
- SQLite database file: `ticketing.db`
- All necessary tables
- Default admin user

### Step 6: Run the Application

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

### Step 7: Access the Application

Open your browser and go to:
```
http://localhost:5000
```

**Default Admin Credentials:**
- Email: `admin@company.com`
- Password: `admin123`

## Production Setup (Using PostgreSQL)

For a production-like environment on your local machine:

### Step 1: Install PostgreSQL

Download and install PostgreSQL from: https://www.postgresql.org/download/

### Step 2: Create Database

Open PostgreSQL command line (psql) or pgAdmin:

```sql
CREATE DATABASE ticketing_db;
CREATE USER ticketing_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ticketing_db TO ticketing_user;
```

### Step 3: Configure Database URL

Edit your `.env` file:

```env
DATABASE_URL=postgresql://ticketing_user:your_password@localhost/ticketing_db
SESSION_SECRET=your-random-secret-key
```

### Step 4: Initialize and Run

```bash
flask init-db
python app.py
```

## Getting Started Guide

### 1. Login as Admin

Navigate to `http://localhost:5000` and login with:
- Email: `admin@company.com`
- Password: `admin123`

### 2. Create Categories

1. Click **Manage → Categories**
2. Create categories for your organization, for example:

**Category 1: Software Installation**
- Description: Software installation and licensing requests
- Keywords: `install, software, application, program, license, teams, zoom, office, adobe`
- Approvers: `manager@company.com, it-director@company.com`

**Category 2: Timesheet Modification**
- Description: Timesheet corrections and modifications
- Keywords: `timesheet, hours, attendance, time, correction, modify, adjust`
- Approvers: `hr-manager@company.com, supervisor@company.com`

**Category 3: Hardware Request**
- Description: Hardware equipment requests
- Keywords: `laptop, desktop, monitor, keyboard, mouse, hardware, equipment, device`
- Approvers: `it-manager@company.com, procurement@company.com`

**Category 4: Access Request**
- Description: System and application access requests
- Keywords: `access, permission, credentials, login, account, rights, privileges`
- Approvers: `security@company.com, manager@company.com`

### 3. Add Team Members

1. Click **Manage → Team Members**
2. Add team members who will work on tickets

Example:
- Name: `John Smith`
- Email: `john.smith@company.com`
- Category: `Software Installation`

Add multiple team members per category for workload distribution.

### 4. Create Regular Users

1. Click **Manage → Users**
2. Create user accounts:
   - Name: `Jane Doe`
   - Email: `jane.doe@company.com`
   - Password: `TempPass123` (they'll change it on first login)
   - Admin User: ☐ (unchecked for regular users)

### 5. Test the System

**As Regular User:**
1. Logout and login as the new user
2. System will force password change on first login
3. Click **New Ticket**
4. Enter a request like:
   ```
   I need Microsoft Teams installed on my work laptop for client meetings. 
   My laptop is Dell Latitude 5420 running Windows 11 Pro. I need this by 
   Friday for an important client call.
   ```
5. Submit the ticket - AI will classify it automatically!

**Email Approvals:**
- Approvers receive email with Approve/Reject links
- After all approvals, ticket is auto-assigned to team member with lowest workload

## Troubleshooting

### Issue: "Module not found" errors

**Solution:** Make sure virtual environment is activated and dependencies are installed
```bash
# Activate venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Issue: Database errors

**Solution:** Reinitialize the database
```bash
# Delete old database
rm ticketing.db  # macOS/Linux
del ticketing.db # Windows

# Reinitialize
flask init-db
```

### Issue: Port 5000 already in use

**Solution:** Change the port in `app.py` (bottom of file):
```python
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)  # Changed to 8000
```

Then access at `http://localhost:8000`

### Issue: AI Classification not working

**Solution:** Check your OpenAI API key
1. Verify `OPENAI_API_KEY` in `.env`
2. Check key is valid at https://platform.openai.com/api-keys
3. System will fall back to keyword matching if API key is missing

### Issue: Gmail emails not sending

**Solution:** Use Gmail App Password
1. Go to Google Account → Security → 2-Step Verification
2. At bottom, click "App passwords"
3. Generate new app password
4. Use this password (not your regular Gmail password) in `.env`

## File Structure

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
├── .env                       # Environment configuration (create this)
├── .env.example              # Environment template
├── ticketing.db              # SQLite database (auto-created)
└── README.md                 # Project documentation
```

## Security Recommendations for Localhost

1. **Change Admin Password**: After first login, change the default admin password
2. **Strong Session Secret**: Use a random, complex `SESSION_SECRET` in `.env`
3. **Secure API Keys**: Never commit `.env` file to version control
4. **Firewall**: For production, configure firewall to restrict access
5. **HTTPS**: For production, use a reverse proxy (nginx) with SSL certificate

## Next Steps

1. Customize categories for your organization
2. Add team members and assign them to categories
3. Create user accounts for your team
4. Test the complete workflow from ticket creation to assignment
5. Configure email settings for production use
6. Consider integrating with Microsoft Teams/Outlook (Phase 2 feature)

## Support

For issues or questions:
- Check the main README.md for detailed feature documentation
- Review the troubleshooting section above
- Check Flask/SQLAlchemy documentation for database issues

## Upgrading to Production

When ready to deploy to production:
1. Switch to PostgreSQL database
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn --bind 0.0.0.0:5000 app:app
   ```
3. Set up nginx as reverse proxy with SSL
4. Configure proper email server (not Gmail)
5. Enable production settings in Flask (`debug=False`)
6. Set strong `SESSION_SECRET` in production `.env`

---

**Happy Ticketing! 🎫**
