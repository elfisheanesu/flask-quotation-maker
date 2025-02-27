from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
from models import Company
from io import BytesIO

def generate_pdf_quotation(quotation, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get company details
    company = Company.get_or_create()
    
    # Add company logo if exists
    if company.logo_filename:
        logo_path = os.path.join('static', 'uploads', company.logo_filename)
        if os.path.exists(logo_path):
            img = Image(logo_path)
            img.drawHeight = 1.25*inch
            img.drawWidth = 1.25*inch
            elements.append(img)
    
    # Company Information
    elements.append(Paragraph(company.name, styles['Heading1']))
    elements.append(Paragraph(company.street_address, styles['Normal']))
    elements.append(Paragraph(f"{company.city}, {company.postal_code}", styles['Normal']))
    elements.append(Paragraph(f"Email: {company.email}", styles['Normal']))
    elements.append(Paragraph(f"Phone: {company.phone}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Quotation Information
    elements.append(Paragraph(f'Quotation #{quotation.id}', styles['Heading2']))
    elements.append(Paragraph(f'Date: {quotation.date.strftime("%Y-%m-%d")}', styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Customer Information
    elements.append(Paragraph('To:', styles['Heading3']))
    elements.append(Paragraph(quotation.customer.name, styles['Normal']))
    elements.append(Paragraph(quotation.customer.email, styles['Normal']))
    elements.append(Paragraph(quotation.customer.phone, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Items Table
    data = [['Item', 'Quantity', 'Unit Price', 'Total']]
    for item in quotation.items:
        data.append([
            item.product.name,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${item.total:.2f}"
        ])
    
    # Add total row
    data.append(['', '', 'Total:', f"${quotation.total:.2f}"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def generate_pdf_invoice(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get company details
    company = Company.get_or_create()
    
    # Add company logo if exists
    if company.logo_filename:
        logo_path = os.path.join('static', 'uploads', company.logo_filename)
        if os.path.exists(logo_path):
            img = Image(logo_path)
            img.drawHeight = 1.25*inch
            img.drawWidth = 1.25*inch
            elements.append(img)
    
    # Company Information
    elements.append(Paragraph(company.name, styles['Heading1']))
    elements.append(Paragraph(company.street_address, styles['Normal']))
    elements.append(Paragraph(f"{company.city}, {company.postal_code}", styles['Normal']))
    elements.append(Paragraph(f"Email: {company.email}", styles['Normal']))
    elements.append(Paragraph(f"Phone: {company.phone}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Invoice Information
    elements.append(Paragraph(f'Invoice #{invoice.id}', styles['Heading2']))
    elements.append(Paragraph(f'Date: {invoice.date.strftime("%Y-%m-%d")}', styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Customer Information
    elements.append(Paragraph('To:', styles['Heading3']))
    elements.append(Paragraph(invoice.quotation.customer.name, styles['Normal']))
    elements.append(Paragraph(invoice.quotation.customer.email, styles['Normal']))
    elements.append(Paragraph(invoice.quotation.customer.phone, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Items Table
    data = [['Item', 'Quantity', 'Unit Price', 'Total']]
    for item in invoice.quotation.items:
        data.append([
            item.product.name,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${item.total:.2f}"
        ])
    
    # Add total row
    data.append(['', '', 'Total:', f"${invoice.total:.2f}"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    # Payment Status
    elements.append(Spacer(1, 20))
    status_style = ParagraphStyle(
        'Status',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.green if invoice.paid else colors.red
    )
    elements.append(Paragraph(f"Status: {'PAID' if invoice.paid else 'UNPAID'}", status_style))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
