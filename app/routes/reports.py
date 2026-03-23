from flask import Blueprint, render_template, send_file, request
from flask_login import login_required, current_user
from app.models import Farm, Sale, SaleEntry, Customer
from app import db
import io
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/sale/<int:sale_id>')
@login_required
def sale_report(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    farm = Farm.query.filter_by(id=sale.farm_id).first_or_404()
    return render_template('reports/sale.html', sale=sale, farm=farm)


@reports_bp.route('/sale/<int:sale_id>/excel')
@login_required
def export_excel(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    farm = Farm.query.filter_by(id=sale.farm_id).first_or_404()

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = 'Sale Report'

    # Colors
    header_fill = PatternFill('solid', start_color='1a472a')
    sub_fill = PatternFill('solid', start_color='2d6a4f')
    total_fill = PatternFill('solid', start_color='d4edda')
    alt_fill = PatternFill('solid', start_color='f0f7f0')

    header_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
    sub_font = Font(name='Arial', bold=True, color='FFFFFF', size=10)
    bold_font = Font(name='Arial', bold=True, size=10)
    normal_font = Font(name='Arial', size=10)
    total_font = Font(name='Arial', bold=True, size=10, color='1a472a')

    thin = Side(style='thin', color='AAAAAA')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    center = Alignment(horizontal='center', vertical='center')
    left = Alignment(horizontal='left', vertical='center')

    def set_cell(cell, value, font=None, fill=None, align=None, bord=None):
        cell.value = value
        if font:
            cell.font = font
        if fill:
            cell.fill = fill
        if align:
            cell.alignment = align
        if bord:
            cell.border = bord

    # Title
    ws.merge_cells('A1:G1')
    set_cell(ws['A1'], '🐔 POULTRY FARM SALE REPORT', Font(name='Arial', bold=True, size=14, color='1a472a'), align=center)
    ws.row_dimensions[1].height = 30

    # Farm & Sale Info
    ws.merge_cells('A3:D3')
    set_cell(ws['A3'], f'Farm: {farm.name}', bold_font, align=left)
    ws.merge_cells('E3:G3')
    set_cell(ws['E3'], f'Sale ID: {sale.sale_code}', bold_font, align=left)

    ws.merge_cells('A4:D4')
    set_cell(ws['A4'], f'Village: {farm.village}, {farm.district}', normal_font, align=left)
    ws.merge_cells('E4:G4')
    set_cell(ws['E4'], f'Date: {sale.sale_date or "N/A"}', normal_font, align=left)

    ws.merge_cells('A5:D5')
    set_cell(ws['A5'], f'Phone: {farm.phone}', normal_font, align=left)
    ws.merge_cells('E5:G5')
    set_cell(ws['E5'], f'Status: {sale.status.upper()}', Font(name='Arial', bold=True, size=10, color='2d6a4f'), align=left)

    if sale.customer:
        ws.merge_cells('A6:D6')
        set_cell(ws['A6'], f'Customer: {sale.customer.name}', normal_font, align=left)
        ws.merge_cells('E6:G6')
        set_cell(ws['E6'], f'Phone: {sale.customer.phone}', normal_font, align=left)
        ws.merge_cells('A7:D7')
        set_cell(ws['A7'], f'Vehicle: {sale.customer.vehicle_number}', normal_font, align=left)

    # Table headers
    headers = ['S.No', 'Empty Boxes', 'Empty Weight (kg)', 'Chickens/Box', 'Load Weight (kg)', 'Total Chickens', 'Net Weight (kg)']
    col_widths = [8, 14, 18, 15, 18, 16, 16]

    row = 9
    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=row, column=col)
        set_cell(cell, h, header_font, header_fill, center, border)
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[row].height = 22

    # Data rows
    total_empty_boxes = 0
    total_empty_weight = 0
    total_chickens_total = 0
    total_load_weight = 0
    total_net_weight = 0

    for i, entry in enumerate(sale.entries, 1):
        row += 1
        total_chickens = entry.empty_boxes * entry.chickens_per_box
        net_weight = entry.load_weight - entry.empty_weight
        fill = alt_fill if i % 2 == 0 else None

        values = [i, entry.empty_boxes, entry.empty_weight, entry.chickens_per_box,
                  entry.load_weight, total_chickens, round(net_weight, 2)]

        total_empty_boxes += entry.empty_boxes
        total_empty_weight += entry.empty_weight
        total_chickens_total += total_chickens
        total_load_weight += entry.load_weight
        total_net_weight += net_weight

        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col)
            set_cell(cell, val, normal_font, fill, center, border)

    # Totals row
    row += 1
    totals = ['TOTAL', total_empty_boxes, round(total_empty_weight, 2), '',
              round(total_load_weight, 2), total_chickens_total, round(total_net_weight, 2)]
    for col, val in enumerate(totals, 1):
        cell = ws.cell(row=row, column=col)
        set_cell(cell, val, total_font, total_fill, center, border)
    ws.row_dimensions[row].height = 20

    # Summary
    row += 2
    avg_weight = total_net_weight / total_chickens_total if total_chickens_total > 0 else 0
    tonnage = total_net_weight / 1000

    summaries = [
        ('Net Weight', f'{round(total_net_weight, 2)} kg'),
        ('Average Weight/Chicken', f'{round(avg_weight, 3)} kg'),
        ('Tonnage', f'{round(tonnage, 4)} ton'),
    ]
    if sale.customer and sale.customer.price_per_kg:
        amount = total_net_weight * sale.customer.price_per_kg
        summaries.append(('Price/kg', f'₹{sale.customer.price_per_kg}'))
        summaries.append(('Total Amount', f'₹{round(amount, 2)}'))

    for label, value in summaries:
        ws.merge_cells(f'A{row}:C{row}')
        set_cell(ws[f'A{row}'], label, bold_font, sub_fill, left)
        ws[f'A{row}'].font = Font(name='Arial', bold=True, size=10, color='FFFFFF')
        ws.merge_cells(f'D{row}:G{row}')
        set_cell(ws[f'D{row}'], value, Font(name='Arial', bold=True, size=11, color='1a472a'), align=center)
        row += 1

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name=f'Sale_{sale.sale_code}_{farm.name}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@reports_bp.route('/sale/<int:sale_id>/pdf')
@login_required
def export_pdf(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    farm = Farm.query.filter_by(id=sale.farm_id).first_or_404()

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    green = colors.HexColor('#1a472a')
    light_green = colors.HexColor('#d4edda')

    title_style = ParagraphStyle('title', parent=styles['Title'], textColor=green, fontSize=18, spaceAfter=6)
    normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontSize=10)
    bold_style = ParagraphStyle('bold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    story = []
    story.append(Paragraph('🐔 Poultry Farm Sale Report', title_style))
    story.append(Spacer(1, 0.3*cm))

    info_data = [
        [Paragraph(f'<b>Farm:</b> {farm.name}', normal_style), Paragraph(f'<b>Sale ID:</b> {sale.sale_code}', normal_style)],
        [Paragraph(f'<b>Location:</b> {farm.village}, {farm.district}', normal_style), Paragraph(f'<b>Date:</b> {sale.sale_date or "N/A"}', normal_style)],
        [Paragraph(f'<b>Phone:</b> {farm.phone}', normal_style), Paragraph(f'<b>Status:</b> {sale.status.upper()}', normal_style)],
    ]
    if sale.customer:
        info_data.append([Paragraph(f'<b>Customer:</b> {sale.customer.name}', normal_style),
                          Paragraph(f'<b>Vehicle:</b> {sale.customer.vehicle_number}', normal_style)])

    info_table = Table(info_data, colWidths=[9*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_green),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    headers = ['S.No', 'Empty\nBoxes', 'Empty Wt\n(kg)', 'Chickens\n/Box', 'Load Wt\n(kg)', 'Total\nChickens', 'Net Wt\n(kg)']
    table_data = [headers]

    total_empty_boxes = 0; total_empty_wt = 0; total_chickens = 0; total_load_wt = 0; total_net_wt = 0

    for i, entry in enumerate(sale.entries, 1):
        tc = entry.empty_boxes * entry.chickens_per_box
        nw = entry.load_weight - entry.empty_weight
        table_data.append([i, entry.empty_boxes, f'{entry.empty_weight:.2f}', entry.chickens_per_box,
                           f'{entry.load_weight:.2f}', tc, f'{nw:.2f}'])
        total_empty_boxes += entry.empty_boxes; total_empty_wt += entry.empty_weight
        total_chickens += tc; total_load_wt += entry.load_weight; total_net_wt += nw

    table_data.append(['TOTAL', total_empty_boxes, f'{total_empty_wt:.2f}', '',
                       f'{total_load_wt:.2f}', total_chickens, f'{total_net_wt:.2f}'])

    col_widths = [1.2*cm, 2*cm, 2.5*cm, 2.3*cm, 2.5*cm, 2.5*cm, 2.5*cm]
    data_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), light_green),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0f7f0')]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(data_table)
    story.append(Spacer(1, 0.5*cm))

    avg_wt = total_net_wt / total_chickens if total_chickens > 0 else 0
    tonnage = total_net_wt / 1000
    summary = [
        ['Net Weight', f'{total_net_wt:.2f} kg'],
        ['Average Weight/Chicken', f'{avg_wt:.3f} kg'],
        ['Tonnage', f'{tonnage:.4f} ton'],
    ]
    if sale.customer and sale.customer.price_per_kg:
        summary.append(['Price per kg', f'₹{sale.customer.price_per_kg}'])
        summary.append(['Total Amount', f'₹{total_net_wt * sale.customer.price_per_kg:.2f}'])

    sum_table = Table(summary, colWidths=[8*cm, 9*cm])
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), green),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, light_green]),
    ]))
    story.append(sum_table)

    doc.build(story)
    output.seek(0)

    return send_file(
        output,
        download_name=f'Sale_{sale.sale_code}_{farm.name}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )
