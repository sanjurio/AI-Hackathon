import os
from flask import url_for
from flask_mail import Mail, Message

mail = Mail()

def send_approval_email(ticket_id, description, category_name, creator_name, approval_token, approver_email):
    if not os.getenv('MAIL_USERNAME'):
        print(f"Email service not configured. Would send approval email to {approver_email} for ticket #{ticket_id}")
        return
    
    try:
        msg = Message(
            subject=f'Ticket Approval Request - #{ticket_id}',
            recipients=[approver_email],
            body=f"""
Hello,

A new ticket requires your approval.

Ticket ID: #{ticket_id}
Description: {description}
Category: {category_name}
Created by: {creator_name}

To approve this ticket, click here:
{url_for('approve_ticket', token=approval_token, action='approve', _external=True)}

To reject this ticket, click here:
{url_for('approve_ticket', token=approval_token, action='reject', _external=True)}

This link is valid for 7 days.

Thank you,
Ticketing System
            """
        )
        mail.send(msg)
        print(f"Approval email sent to {approver_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_assignment_email(ticket_id, description, category_name, creator_name, team_member_name, team_member_email):
    if not os.getenv('MAIL_USERNAME'):
        print(f"Email service not configured. Would send assignment email to {team_member_email} for ticket #{ticket_id}")
        return
    
    try:
        msg = Message(
            subject=f'New Ticket Assigned - #{ticket_id}',
            recipients=[team_member_email],
            body=f"""
Hello {team_member_name},

A new ticket has been assigned to you.

Ticket ID: #{ticket_id}
Description: {description}
Category: {category_name}
Created by: {creator_name}
Priority: Normal

Please log in to the ticketing system to view details and update the status.

Thank you,
Ticketing System
            """
        )
        mail.send(msg)
        print(f"Assignment email sent to {team_member_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
