from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os

class ReceiptService:
    @staticmethod
    def generate_receipt_pdf(ride, payment):
        """Generate PDF receipt for a completed ride"""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Title
        title = Paragraph("RideShare Receipt", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Receipt details
        receipt_data = [
            ['Receipt ID:', payment.transaction_id],
            ['Date:', payment.processed_at.strftime('%Y-%m-%d %I:%M %p')],
            ['Ride ID:', str(ride.id)],
            ['Status:', 'Completed'],
            ['', ''],
            ['Pickup:', ride.pickup_address],
            ['Dropoff:', ride.dropoff_address],
            ['Distance:', f"{ride.distance_km} km"],
            ['Duration:', f"{ride.estimated_duration} minutes"],
            ['', ''],
            ['Rider:', f"{ride.rider.first_name or ''} {ride.rider.last_name or ''}".strip()],
            ['Driver:', f"{ride.driver.first_name or ''} {ride.driver.last_name or ''}".strip()],
            ['', ''],
            ['Amount Paid:', f"${payment.amount:.2f}"],
            ['Payment Method:', payment.payment_method.title()],
        ]
        
        # Create table
        table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer = Paragraph("Thank you for using RideShare!", styles['Normal'])
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    @staticmethod
    def generate_receipt_text(ride, payment):
        """Generate text receipt for a completed ride"""
        receipt_text = f"""
RideShare Receipt
================

Receipt ID: {payment.transaction_id}
Date: {payment.processed_at.strftime('%Y-%m-%d %I:%M %p')}
Ride ID: {ride.id}
Status: Completed

Trip Details:
Pickup: {ride.pickup_address}
Dropoff: {ride.dropoff_address}
Distance: {ride.distance_km} km
Duration: {ride.estimated_duration} minutes

People:
Rider: {ride.rider.first_name or ''} {ride.rider.last_name or ''}
Driver: {ride.driver.first_name or ''} {ride.driver.last_name or ''}

Payment:
Amount Paid: ${payment.amount:.2f}
Payment Method: {payment.payment_method.title()}

Thank you for using RideShare!
        """
        
        return receipt_text.strip()
