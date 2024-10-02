@app.route('/generate_excel')
def generate_excel():
    wb = Workbook()

    # ... (previous code remains the same)

    # Proposals sheet
    ws_proposals = wb.active
    ws_proposals.title = "Proposals"
    ws_proposals.append(["Month", "ID", "Name", "Team Leader", "Status", "Description", "Due Date"])

    proposals = Proposal.query.order_by(Proposal.due_date).all()
    current_month = None

    for proposal in proposals:
        proposal_month = proposal.due_date.strftime('%B %Y') if proposal.due_date else "No Due Date"

        if proposal_month != current_month:
            current_month = proposal_month
            ws_proposals.append([current_month])

        ws_proposals.append([
            "",  # Leave the month column empty for non-header rows
            proposal.id,
            proposal.name,
            proposal.team_leader.name if proposal.team_leader else "N/A",
            proposal.status,
            proposal.description,
            proposal.due_date.strftime('%d{} %b %Y').format(
                get_ordinal_suffix(proposal.due_date.day)) if proposal.due_date else "N/A"
        ])
    style_sheet(ws_proposals, proposal_color)

    # Engagements sheet
    ws_engagements = wb.create_sheet("Engagements")
    ws_engagements.append(["ID", "Name", "Team Leader", "Status", "Description", "Start Date", "End Date"])
    for engagement in Engagement.query.all():
        ws_engagements.append([
            engagement.id,
            engagement.name,
            engagement.team_leader.name if engagement.team_leader else "N/A",
            engagement.status,
            engagement.description,
            engagement.start_date.strftime('%d{} %b %Y').format(
                get_ordinal_suffix(engagement.start_date.day)) if engagement.start_date else "N/A",
            engagement.end_date.strftime('%d{} %b %Y').format(
                get_ordinal_suffix(engagement.end_date.day)) if engagement.end_date else "N/A"
        ])
    style_sheet(ws_engagements, engagement_color)

    # ... (rest of the code remains the same)


# Add this function at the beginning of your script
def get_ordinal_suffix(day):
    if 11 <= day <= 13:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')