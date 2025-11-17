from models import TeamMember, Ticket

def assign_ticket_to_team_member(ticket):
    if not ticket.category_id:
        return None
    
    team_members = TeamMember.query.filter_by(
        category_id=ticket.category_id,
        is_available=True
    ).all()
    
    if not team_members:
        return None
    
    member_ticket_counts = {}
    for member in team_members:
        active_tickets = Ticket.query.filter(
            Ticket.assigned_to == member.id,
            Ticket.status.in_(['Assigned', 'In Progress'])
        ).count()
        member_ticket_counts[member.id] = active_tickets
    
    least_loaded_member = min(team_members, key=lambda m: member_ticket_counts[m.id])
    
    return least_loaded_member
