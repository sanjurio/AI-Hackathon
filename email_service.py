import os
import resend
from flask import url_for

def get_resend_api_key():
    """Get Resend API key from Replit connection or environment"""
    api_key = os.getenv('RESEND_API_KEY')
    if not api_key:
        raise ValueError("RESEND_API_KEY not found in environment variables")
    return api_key

def send_approval_email(ticket_id, description, category_name, creator_name, approval_token, approver_email):
    """Send approval request email via Resend"""
    try:
        resend.api_key = get_resend_api_key()
        
        from_email = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        
        params = {
            "from": from_email,
            "to": [approver_email],
            "subject": f'Ticket Approval Request - #{ticket_id}',
            "html": f"""
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
        }
        
        email = resend.Emails.send(params)
        print(f"✓ Approval email sent to {approver_email} (Email ID: {email.get('id', 'N/A')})")
        return True
    except Exception as e:
        print(f"✗ Failed to send approval email to {approver_email}: {e}")
        return False

def send_assignment_email(ticket_id, description, category_name, creator_name, team_member_name, team_member_email):
    """Send ticket assignment email via Resend"""
    try:
        resend.api_key = get_resend_api_key()
        
        from_email = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        
        params = {
            "from": from_email,
            "to": [team_member_email],
            "subject": f'New Ticket Assigned - #{ticket_id}',
            "html": f"""
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
        }
        
        email = resend.Emails.send(params)
        print(f"✓ Assignment email sent to {team_member_email} (Email ID: {email.get('id', 'N/A')})")
        return True
    except Exception as e:
        print(f"✗ Failed to send assignment email to {team_member_email}: {e}")
        return False
