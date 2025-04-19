import os
import uuid
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from models import Product, ProductAttribute, AttributeDefinition, ProductImage, InventoryLog

def generate_sku():
    """Generate a unique SKU."""
    prefix = "PUMA"
    timestamp = datetime.now().strftime("%y%m%d")
    random_string = uuid.uuid4().hex[:4].upper()
    return f"{prefix}-{timestamp}-{random_string}"

def save_barcode_image(file):
    """Save an uploaded barcode image and return the file path.
    
    This function is used for storing GS1's Digital Link 2D barcodes that are uploaded
    for each item rather than being generated within the system.
    """
    if file and allowed_file(file.filename):
        try:
            # Create a unique filename
            original_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"barcode_{uuid.uuid4().hex}.{original_ext}"
            
            # Create upload directory if it doesn't exist
            upload_folder = current_app.config['UPLOAD_FOLDER']
            barcode_folder = os.path.join(upload_folder, 'barcodes')
            os.makedirs(barcode_folder, exist_ok=True)
            
            file_path = os.path.join(barcode_folder, filename)
            
            # Save the barcode image
            file.save(file_path)
            
            return os.path.join('static', 'uploads', 'barcodes', filename)
        except Exception as e:
            current_app.logger.error(f"Barcode image save error: {e}")
            return None
    return None

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file):
    """Save an image and return the file path."""
    if file and allowed_file(file.filename):
        try:
            # Create a unique filename
            filename = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
            
            # Create upload directory if it doesn't exist
            upload_folder = current_app.config['UPLOAD_FOLDER']
            images_folder = os.path.join(upload_folder, 'images')
            os.makedirs(images_folder, exist_ok=True)
            
            file_path = os.path.join(images_folder, filename)
            
            # Resize and save the image
            img = Image.open(file)
            img = img.resize((800, 800), Image.LANCZOS)
            img.save(file_path)
            
            return os.path.join('static', 'uploads', 'images', filename)
        except Exception as e:
            current_app.logger.error(f"Image save error: {e}")
            return None
    return None

def generate_inventory_pdf(data, filename):
    """Generate PDF report for inventory data."""
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12
    )
    
    # Content elements
    elements = []
    
    # Add title
    title = Paragraph(f"Puma Warehouse Inventory Report - {datetime.now().strftime('%Y-%m-%d')}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.25*inch))
    
    # Table header
    table_data = [["SKU", "Name", "Quantity", "Category", "Size", "Color", "Price"]]
    
    # Add data rows
    for item in data:
        table_data.append([
            item.sku,
            item.name,
            str(item.quantity),
            item.category,
            item.size,
            item.color,
            f"${item.price_sell:.2f}"
        ])
    
    # Create and style the table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    
    # Add footer
    elements.append(Spacer(1, 0.5*inch))
    footer = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"])
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    return os.path.join('static', 'uploads', 'reports', filename)

def export_to_excel(data, filename):
    """Export data to Excel file."""
    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', filename)
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    # Convert data to DataFrame
    records = []
    for item in data:
        record = {
            'SKU': item.sku,
            'Name': item.name,
            'Barcode': item.barcode,
            'Category': item.category,
            'Size': item.size,
            'Color': item.color,
            'Gender': item.gender,
            'Material': item.material,
            'Quantity': item.quantity,
            'Cost Price': item.price_cost,
            'Selling Price': item.price_sell,
            'Location': item.location
        }
        
        # Add dynamic attributes
        attribute_defs = AttributeDefinition.query.all()
        for attr_def in attribute_defs:
            attr = ProductAttribute.query.filter_by(
                product_id=item.id, 
                attribute_id=attr_def.id
            ).first()
            
            record[attr_def.name] = attr.value if attr else ""
        
        records.append(record)
    
    df = pd.DataFrame(records)
    df.to_excel(excel_path, index=False)
    
    return os.path.join('static', 'uploads', 'reports', filename)

def parse_excel_import(file_path):
    """Parse Excel file for product import."""
    try:
        df = pd.read_excel(file_path)
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        
        # Process each record to validate and extract data
        processed_records = []
        for record in records:
            # Skip rows with no SKU or Name
            if not pd.notna(record.get('SKU')) or not pd.notna(record.get('Name')):
                continue
            
            processed_record = {
                'sku': str(record.get('SKU', '')).strip(),
                'name': str(record.get('Name', '')).strip(),
                'barcode': str(record.get('Barcode', '')).strip() if pd.notna(record.get('Barcode')) else None,
                'category': str(record.get('Category', '')).strip() if pd.notna(record.get('Category')) else None,
                'size': str(record.get('Size', '')).strip() if pd.notna(record.get('Size')) else None,
                'color': str(record.get('Color', '')).strip() if pd.notna(record.get('Color')) else None,
                'gender': str(record.get('Gender', '')).strip() if pd.notna(record.get('Gender')) else None,
                'material': str(record.get('Material', '')).strip() if pd.notna(record.get('Material')) else None,
                'price_cost': float(record.get('Cost Price', 0)) if pd.notna(record.get('Cost Price')) else 0,
                'price_sell': float(record.get('Selling Price', 0)) if pd.notna(record.get('Selling Price')) else 0,
                'quantity': int(record.get('Quantity', 0)) if pd.notna(record.get('Quantity')) else 0,
                'location': str(record.get('Location', '')).strip() if pd.notna(record.get('Location')) else None,
                'image_url': str(record.get('Image URL', '')).strip() if pd.notna(record.get('Image URL')) else None,
                'attributes': {}
            }
            
            # Extract dynamic attributes (columns that are not standard)
            standard_columns = ['SKU', 'Name', 'Barcode', 'Category', 'Size', 'Color', 'Gender', 
                               'Material', 'Quantity', 'Cost Price', 'Selling Price', 'Location', 'Image URL']
            
            for col, value in record.items():
                if col not in standard_columns and pd.notna(value):
                    processed_record['attributes'][str(col)] = str(value).strip()
            
            processed_records.append(processed_record)
        
        return processed_records
    
    except Exception as e:
        current_app.logger.error(f"Excel import error: {e}")
        return None
