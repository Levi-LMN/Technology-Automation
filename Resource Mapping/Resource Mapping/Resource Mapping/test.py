@app.route('/generate_excel')
def generate_excel():
    wb = Workbook()

    # Color codes and styles
    proposal_color = PatternFill(start_color="FFB3E5FC", end_color="FFB3E5FC", fill_type="solid")
    engagement_color = PatternFill(start_color="FFFFCCCB", end_color="FFFFCCCB", fill_type="solid")
    non_billable_color = PatternFill(start_color="FFD7F6D3", end_color="FFD7F6D3", fill_type="solid")
    total_color = PatternFill(start_color="FFFFD700", end_color="FFFFD700", fill_type="solid")
    header_fill = PatternFill(start_color="FFD3D3D3", end_color="FFD3D3D3", fill_type="solid")
    leave_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

    header_font = Font(bold=True, size=12)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    def style_sheet(ws, color_fill):
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = border
                if cell.row == 1:
                    cell.fill = header_fill
                    cell.font = header_font
                else:
                    cell.fill = color_fill

        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width

    # Proposals sheet
    ws_proposals = wb.active
    ws_proposals.title = "Proposals"
    ws_proposals.append(["ID", "Name", "Team Leader", "Status", "Description", "Due Date"])
    for proposal in Proposal.query.all():
        ws_proposals.append([
            proposal.id,
            proposal.name,
            proposal.team_leader.name if proposal.team_leader else "N/A",
            proposal.status,
            proposal.description,
            proposal.due_date.strftime('%Y-%m-%d') if proposal.due_date else "N/A"
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
            engagement.start_date.strftime('%Y-%m-%d') if engagement.start_date else "N/A",
            engagement.end_date.strftime('%Y-%m-%d') if engagement.end_date else "N/A"
        ])
    style_sheet(ws_engagements, engagement_color)

    # Non-Billables sheet
    ws_non_billables = wb.create_sheet("Non-Billables")
    ws_non_billables.append(["ID", "Name"])
    for non_billable in NonBillable.query.all():
        ws_non_billables.append([non_billable.id, non_billable.name])
    style_sheet(ws_non_billables, non_billable_color)

    # Staff Members sheet
    ws_staff = wb.create_sheet("Staff Members")

    # Get all unique months from HoursLog
    unique_months = db.session.query(
        db.func.strftime('%Y-%m', HoursLog.date).label('month')
    ).distinct().order_by('month').all()

    current_row = 1

    # Get all staff members
    all_staff = Staff.query.all()

    for month_tuple in unique_months:
        month = datetime.strptime(month_tuple[0], '%Y-%m')
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        ws_staff.cell(row=current_row, column=1, value=f"Month: {month.strftime('%B %Y')}")
        ws_staff.cell(row=current_row, column=1).font = Font(bold=True, size=14)
        current_row += 1

        headers = ["ID", "Name", "Engagements", "Proposals", "Non-Billables", "Total Hours", "Category"]
        for col, header in enumerate(headers, start=1):
            cell = ws_staff.cell(row=current_row, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
        current_row += 1

        for staff in all_staff:
            month_logs = HoursLog.query.filter(
                HoursLog.staff_id == staff.id,
                HoursLog.date >= month_start,
                HoursLog.date <= month_end
            ).all()

            if month_logs:
                logged_engagements = set(
                    Engagement.query.get(log.item_id).name for log in month_logs if log.category == 'engagement')
                logged_proposals = set(
                    Proposal.query.get(log.item_id).name for log in month_logs if log.category == 'proposal')

                engagements = ", ".join(logged_engagements)
                proposals = ", ".join(logged_proposals)
                non_billable_hours = sum([log.hours for log in month_logs if log.category == 'non_billable'])
                total_hours = sum([log.hours for log in month_logs])

                if logged_engagements:
                    primary_category = "Engagement"
                elif logged_proposals:
                    primary_category = "Proposal"
                else:
                    primary_category = "Non-Billable"
            else:
                engagements = ""
                proposals = ""
                non_billable_hours = 0
                total_hours = 0
                primary_category = ""

            row_data = [
                staff.id,
                staff.name,
                engagements,
                proposals,
                f"{non_billable_hours:.2f} hours" if non_billable_hours > 0 else "",
                f"{total_hours:.2f} hours" if total_hours > 0 else "",
                primary_category
            ]

            for col, value in enumerate(row_data, start=1):
                cell = ws_staff.cell(row=current_row, column=col, value=value)
                if col == 7:  # Category column
                    if value == "Engagement":
                        cell.fill = engagement_color
                    elif value == "Proposal":
                        cell.fill = proposal_color
                    elif value == "Non-Billable":
                        cell.fill = non_billable_color

            current_row += 1

        current_row += 2  # Add space between tables

    # Adjust column widths
    for column in ws_staff.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws_staff.column_dimensions[column_letter].width = adjusted_width

    # Generate monthly sheets
    ke_holidays = holidays.KE()

    earliest_date = db.session.query(db.func.min(HoursLog.date)).scalar()
    if earliest_date is None:
        earliest_date = datetime.now().date().replace(day=1)

    current_year = datetime.now().year
    if datetime.now().month > 6:
        end_financial_year = datetime(current_year + 1, 6, 30).date()
    else:
        end_financial_year = datetime(current_year, 6, 30).date()

    current_date = earliest_date.replace(day=1)
    while current_date <= end_financial_year:
        month_name = current_date.strftime('%B %Y')
        ws_month = wb.create_sheet(month_name)

        header_fill = PatternFill(start_color="FFD3D3D3", end_color="FFD3D3D3", fill_type="solid")
        subheader_fill = PatternFill(start_color="FFF0F0F0", end_color="FFF0F0F0", fill_type="solid")
        holiday_fill = PatternFill(start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        header_font = Font(bold=True, size=12)
        subheader_font = Font(bold=True, size=11)

        columns = ["Staff Name"]
        categories = ["Proposals", "Engagements", "Non-Billables", "Total"]

        working_days = []
        month_end = current_date.replace(day=calendar.monthrange(current_date.year, current_date.month)[1])
        current = max(current_date, earliest_date)
        while current <= month_end:
            if current.weekday() < 5:
                working_days.append(current)
            current += timedelta(days=1)

        for day in working_days:
            date_header = f"{day.strftime('%A %d %B %Y')}"
            columns.extend([date_header] + ['' for _ in range(len(categories) - 1)])
        ws_month.append(columns)

        sub_headers = [""]
        for _ in range(len(working_days)):
            sub_headers.extend(categories)
        ws_month.append(sub_headers)

        # Style and format headers
        for row in ws_month[1:3]:
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        for col in range(1, len(columns) + 1):
            header_cell = ws_month.cell(row=1, column=col)
            subheader_cell = ws_month.cell(row=2, column=col)

            header_cell.fill = header_fill
            header_cell.font = header_font
            subheader_cell.fill = subheader_fill
            subheader_cell.font = subheader_font

            if col > 1 and (col - 2) % 4 == 0:
                ws_month.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col + 3)

            if subheader_cell.value == "Proposals":
                subheader_cell.fill = proposal_color
            elif subheader_cell.value == "Engagements":
                subheader_cell.fill = engagement_color
            elif subheader_cell.value == "Non-Billables":
                subheader_cell.fill = non_billable_color
            elif subheader_cell.value == "Total":
                subheader_cell.fill = total_color

            if col > 1 and (col - 2) % 4 == 0:
                date_str = header_cell.value.split(' ', 1)[1]
                date = datetime.strptime(date_str, '%d %B %Y').date()
                if date in ke_holidays:
                    header_cell.fill = holiday_fill
                    header_cell.font = Font(bold=True, color="FFFFFFFF")
                    ws_month.cell(row=1, column=col, value=f"{header_cell.value} (Holiday: {ke_holidays.get(date)})")

        ws_month.row_dimensions[1].height = 30
        ws_month.row_dimensions[2].height = 25

        # Start adding data from row 3
