import os
from flask import url_for
from flask_mail import Mail, Message

mail = Mail()

def send_approval_email(ticket, approver_email):
    if not os.getenv('MAIL_USERNAME'):
        print(f"Email service not configured. Would send approval email to {approver_email} for ticket #{ticket.id}")
        return
    
    try:
        msg = Message(
            subject=f'Ticket Approval Request - #{ticket.id}',
            recipients=[approver_email],
            body=f"""
Hello,

A new ticket requires your approval.

Ticket ID: #{ticket.id}
Description: {ticket.description}
Category: {ticket.category.name if ticket.category else 'Uncategorized'}
Created by: {ticket.creator.name}

To approve this ticket, click here:
{url_for('approve_ticket', ticket_id=ticket.id, approval_id=ticket.approvals[-1].id, action='approve', _external=True)}

To reject this ticket, click here:
{url_for('approve_ticket', ticket_id=ticket.id, approval_id=ticket.approvals[-1].id, action='reject', _external=True)}

Thank you,
Ticketing System
            """
        )
        mail.send(msg)
        print(f"Approval email sent to {approver_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_assignment_email(ticket, team_member):
    if not os.getenv('MAIL_USERNAME'):
        print(f"Email service not configured. Would send assignment email to {team_member.email} for ticket #{ticket.id}")
        return
    
    try:
        msg = Message(
            subject=f'New Ticket Assigned - #{ticket.id}',
            recipients=[team_member.email],
            body=f"""
Hello {team_member.name},

A new ticket has been assigned to you.

Ticket ID: #{ticket.id}
Description: {ticket.description}
Category: {ticket.category.name if ticket.category else 'Uncategorized'}
Created by: {ticket.creator.name}
Priority: Normal

Please log in to the ticketing system to view details and update the status.

Thank you,
Ticketing System
            """
        )
        mail.send(msg)
        print(f"Assignment email sent to {team_member.email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
