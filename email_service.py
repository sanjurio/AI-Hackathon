import os
from flask import url_for
from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    
    mail.init_app(app)
    
    if app.config['MAIL_USERNAME']:
        print(f"✓ Email configured with {app.config['MAIL_USERNAME']}")
    else:
        print("✗ Email not configured - missing MAIL_USERNAME")

def get_email_configured():
    """Check if email is configured"""
    return os.getenv('MAIL_USERNAME') is not None

def send_approval_email(ticket_id, description, category_name, creator_name, approval_token, approver_email):
    """Send approval request email via SMTP"""
    try:
        if not get_email_configured():
            print(f"✗ Email not configured - skipping email to {approver_email}")
            return False
        
        print(f"📧 Attempting to send approval email to {approver_email} for ticket #{ticket_id}")
        
        msg = Message(
            subject=f'Ticket Approval Request - #{ticket_id}',
            recipients=[approver_email]
        )
        
        msg.html = f"""
        <html>
        <body>
            <h2>Ticket Approval Request</h2>
            <p>Hello,</p>
            <p>A new ticket requires your approval.</p>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Ticket ID:</td>
                    <td style="padding: 8px;">#{ticket_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Description:</td>
                    <td style="padding: 8px;">{description}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Category:</td>
                    <td style="padding: 8px;">{category_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Created by:</td>
                    <td style="padding: 8px;">{creator_name}</td>
                </tr>
            </table>
            <p>
                <a href="{url_for('approve_ticket', token=approval_token, action='approve', _external=True)}" 
                   style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-right: 10px;">
                    Approve Ticket
                </a>
                <a href="{url_for('approve_ticket', token=approval_token, action='reject', _external=True)}" 
                   style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reject Ticket
                </a>
            </p>
            <p style="color: #666; font-size: 12px;">This link is valid for 7 days.</p>
            <p>Thank you,<br>Ticketing System</p>
        </body>
        </html>
        """
        
        print(f"📧 Sending email via {os.getenv('MAIL_SERVER', 'smtp.gmail.com')}:{os.getenv('MAIL_PORT', '587')}")
        mail.send(msg)
        print(f"✓ Approval email sent successfully to {approver_email}")
        return True
    except Exception as e:
        import traceback
        print(f"✗ Failed to send approval email to {approver_email}: {e}")
        print(f"   Error details: {traceback.format_exc()}")
        return False

def send_assignment_email(ticket_id, description, category_name, creator_name, team_member_name, team_member_email):
    """Send ticket assignment email via SMTP"""
    try:
        if not get_email_configured():
            print(f"✗ Email not configured - skipping email to {team_member_email}")
            return False
        
        msg = Message(
            subject=f'New Ticket Assigned - #{ticket_id}',
            recipients=[team_member_email]
        )
        
        msg.html = f"""
        <html>
        <body>
            <h2>New Ticket Assigned</h2>
            <p>Hello {team_member_name},</p>
            <p>A new ticket has been assigned to you.</p>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Ticket ID:</td>
                    <td style="padding: 8px;">#{ticket_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Description:</td>
                    <td style="padding: 8px;">{description}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Category:</td>
                    <td style="padding: 8px;">{category_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Created by:</td>
                    <td style="padding: 8px;">{creator_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Priority:</td>
                    <td style="padding: 8px;">Normal</td>
                </tr>
            </table>
            <p>Please log in to the ticketing system to view details and update the status.</p>
            <p>Thank you,<br>Ticketing System</p>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"✓ Assignment email sent to {team_member_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send assignment email to {team_member_email}: {e}")
        return False
