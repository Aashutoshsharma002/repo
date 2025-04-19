import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required
from app import db
from models import Product, InventoryLog
from utils import generate_inventory_pdf, export_to_excel
from datetime import datetime, timedelta
import pandas as pd

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    """Reports dashboard."""
    return render_template('reports/inventory.html')

@bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    """Generate inventory report."""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        category = request.form.get('category', '')
        
        # Get products based on category filter
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        products = query.order_by(Product.name).all()
        
        if not products:
            flash('No products found for the selected criteria', 'warning')
            return redirect(url_for('reports.inventory'))
        
        if report_type == 'pdf':
            # Generate PDF report
            filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = generate_inventory_pdf(products, filename)
            
            return send_file(pdf_path, as_attachment=True)
        else:
            # Generate Excel report
            filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            excel_path = export_to_excel(products, filename)
            
            return send_file(excel_path, as_attachment=True)
    
    # Get categories for filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    # Calculate inventory stats by category
    category_stats = {}
    total_stats = {'count': 0, 'quantity': 0, 'value': 0}
    
    for category in categories:
        products = Product.query.filter_by(category=category).all()
        count = len(products)
        quantity = sum(p.quantity for p in products)
        value = sum(p.price_sell * p.quantity for p in products)
        
        category_stats[category] = {
            'count': count,
            'quantity': quantity,
            'value': value
        }
        
        total_stats['count'] += count
        total_stats['quantity'] += quantity
        total_stats['value'] += value
    
    # Get data for the pie chart
    category_quantities = [stats['quantity'] for stats in category_stats.values()]
    
    return render_template('reports/inventory.html', 
                          categories=categories,
                          category_stats=category_stats,
                          total_stats=total_stats,
                          category_quantities=category_quantities)

@bp.route('/monthly', methods=['GET', 'POST'])
@login_required
def monthly():
    """Generate monthly inventory movement report."""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        month = request.form.get('month')
        year = request.form.get('year')
        
        # Validate input
        if not month or not year:
            flash('Month and year are required', 'danger')
            return redirect(url_for('reports.monthly'))
        
        try:
            # Create date range for the selected month
            start_date = datetime(int(year), int(month), 1)
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(int(year), int(month) + 1, 1) - timedelta(days=1)
        except ValueError:
            flash('Invalid month or year', 'danger')
            return redirect(url_for('reports.monthly'))
        
        # Get inventory logs for the selected month
        logs = InventoryLog.query.filter(
            InventoryLog.created_at.between(start_date, end_date)
        ).order_by(InventoryLog.created_at).all()
        
        if not logs:
            flash('No inventory movements found for the selected month', 'warning')
            return redirect(url_for('reports.monthly'))
        
        # Organize data by product
        product_movements = {}
        
        for log in logs:
            product = Product.query.get(log.product_id)
            if not product:
                continue
                
            if product.id not in product_movements:
                product_movements[product.id] = {
                    'sku': product.sku,
                    'name': product.name,
                    'category': product.category,
                    'stock_in': 0,
                    'stock_out': 0,
                    'adjustments': 0,
                    'net_change': 0
                }
            
            if log.action_type == 'in':
                product_movements[product.id]['stock_in'] += log.quantity
                product_movements[product.id]['net_change'] += log.quantity
            elif log.action_type == 'out':
                product_movements[product.id]['stock_out'] += log.quantity
                product_movements[product.id]['net_change'] -= log.quantity
            elif log.action_type == 'adjust':
                product_movements[product.id]['adjustments'] += log.quantity
                product_movements[product.id]['net_change'] += log.quantity
        
        # Create DataFrame for easy export
        df = pd.DataFrame.from_dict(product_movements, orient='index')
        
        # Generate file path and folder
        os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports'), exist_ok=True)
        
        if report_type == 'pdf':
            # Generate PDF report
            filename = f"monthly_report_{year}_{month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', filename)
            
            # Create PDF with ReportLab
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            
            # Title
            styles = getSampleStyleSheet()
            month_name = datetime(int(year), int(month), 1).strftime('%B')
            elements.append(Paragraph(f"Monthly Inventory Report - {month_name} {year}", styles['Heading1']))
            elements.append(Spacer(1, 20))
            
            # Summary Table
            data = [['SKU', 'Product Name', 'Category', 'Stock In', 'Stock Out', 'Adjustments', 'Net Change']]
            
            for product_id, movement in product_movements.items():
                data.append([
                    movement['sku'],
                    movement['name'],
                    movement['category'],
                    movement['stock_in'],
                    movement['stock_out'],
                    movement['adjustments'],
                    movement['net_change']
                ])
            
            # Add totals row
            totals = ['TOTAL', '', '']
            totals.append(sum(m['stock_in'] for m in product_movements.values()))
            totals.append(sum(m['stock_out'] for m in product_movements.values()))
            totals.append(sum(m['adjustments'] for m in product_movements.values()))
            totals.append(sum(m['net_change'] for m in product_movements.values()))
            data.append(totals)
            
            # Create and style table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
        else:
            # Export to Excel
            filename = f"monthly_report_{year}_{month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', filename)
            
            # Add totals row
            df.loc['TOTAL'] = [
                'TOTAL',
                'Total',
                'All Categories',
                df['stock_in'].sum(),
                df['stock_out'].sum(),
                df['adjustments'].sum(),
                df['net_change'].sum()
            ]
            
            # Export to Excel
            df.to_excel(file_path)
        
        return send_file(file_path, as_attachment=True)
    
    # Get current month and year for default selection
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Create month choices
    months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    
    # Create year choices (last 5 years)
    years = list(range(current_year - 4, current_year + 1))
    
    return render_template('reports/monthly.html', 
                          months=months, 
                          years=years,
                          current_month=current_month,
                          current_year=current_year)

@bp.route('/low-stock')
@login_required
def low_stock():
    """Generate low stock report."""
    threshold = request.args.get('threshold', 10, type=int)
    report_type = request.args.get('report_type', 'html')
    
    # Get low stock products
    low_stock_products = Product.query.filter(
        Product.quantity <= threshold
    ).order_by(Product.quantity).all()
    
    if not low_stock_products and report_type == 'html':
        flash('No low stock products found', 'info')
        return render_template('reports/low_stock.html', threshold=threshold)
    
    if report_type == 'pdf':
        # Generate PDF report
        filename = f"low_stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = generate_inventory_pdf(low_stock_products, filename)
        
        return send_file(pdf_path, as_attachment=True)
    elif report_type == 'excel':
        # Generate Excel report
        filename = f"low_stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_path = export_to_excel(low_stock_products, filename)
        
        return send_file(excel_path, as_attachment=True)
    else:
        # HTML report
        return render_template('reports/low_stock.html', 
                              products=low_stock_products,
                              threshold=threshold)
