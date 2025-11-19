import os
import resend
import requests
from flask import url_for

def get_resend_credentials():
    """Get Resend credentials from Replit connector"""
    try:
        hostname = os.getenv('CONNECTORS_HOSTNAME', 'connectors.replit.com')
        repl_identity = os.getenv('REPL_IDENTITY')
        
        if not repl_identity:
            raise ValueError("REPL_IDENTITY not found - cannot access Replit connector")
        
        x_replit_token = f'repl {repl_identity}'
        
        response = requests.get(
            f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=resend',
            headers={
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': x_replit_token
            },
            timeout=10
        )
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch Resend credentials: {response.status_code}")
        
        data = response.json()
        items = data.get('items', [])
        
        if not items or not items[0].get('settings', {}).get('api_key'):
            raise ValueError("Resend not connected or API key not found")
        
        settings = items[0]['settings']
        return {
            'api_key': settings['api_key'],
            'from_email': settings.get('from_email', 'onboarding@resend.dev')
        }
    except Exception as e:
        print(f"✗ Failed to get Resend credentials: {e}")
        return None

def send_approval_email(ticket_id, description, category_name, creator_name, approval_token, approver_email):
    """Send approval request email via Resend"""
    try:
        credentials = get_resend_credentials()
        if not credentials:
            raise ValueError("Failed to get Resend credentials")
        
        resend.api_key = credentials['api_key']
        from_email = credentials['from_email']
        
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
        credentials = get_resend_credentials()
        if not credentials:
            raise ValueError("Failed to get Resend credentials")
        
        resend.api_key = credentials['api_key']
        from_email = credentials['from_email']
        
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
