from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import Product, InventoryLog
from datetime import datetime

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
@login_required
def index():
    """Inventory management dashboard."""
    # Get low stock items (quantity less than 10)
    low_stock = Product.query.filter(Product.quantity < 10).order_by(Product.quantity).limit(5).all()
    
    # Get recent inventory activities
    recent_activities = InventoryLog.query.order_by(InventoryLog.created_at.desc()).limit(10).all()
    
    # Get total product count and total inventory value
    total_products = Product.query.count()
    total_value = db.session.query(db.func.sum(Product.quantity * Product.price_cost)).scalar() or 0
    
    return render_template('inventory/scan.html', 
                          low_stock=low_stock,
                          recent_activities=recent_activities,
                          total_products=total_products,
                          total_value=total_value)

@bp.route('/stock-in', methods=['GET', 'POST'])
@login_required
def stock_in():
    """Handle stock-in operations."""
    # Only staff can perform stock-in
    if not current_user.is_staff():
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('inventory.index'))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        reason = request.form.get('reason')
        
        # Validate input
        error = None
        if not product_id:
            error = 'Product is required'
        elif not quantity or not quantity.isdigit() or int(quantity) <= 0:
            error = 'Valid quantity is required'
        elif not reason:
            error = 'Reason is required'
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('inventory.stock_in'))
        
        # Get product and update quantity
        product = Product.query.get_or_404(product_id)
        quantity = int(quantity)
        
        # Create inventory log
        log = InventoryLog(
            product_id=product.id,
            action_type='in',
            quantity=quantity,
            reason=reason,
            created_by=current_user.id
        )
        
        # Update product quantity
        product.quantity += quantity
        
        db.session.add(log)
        db.session.commit()
        
        flash(f'Successfully added {quantity} units of {product.name}', 'success')
        return redirect(url_for('inventory.index'))
    
    # For GET request, show form with product selection
    return render_template('inventory/stock_in.html')

@bp.route('/stock-out', methods=['GET', 'POST'])
@login_required
def stock_out():
    """Handle stock-out operations."""
    # Only staff can perform stock-out
    if not current_user.is_staff():
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('inventory.index'))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        reason = request.form.get('reason')
        
        # Validate input
        error = None
        if not product_id:
            error = 'Product is required'
        elif not quantity or not quantity.isdigit() or int(quantity) <= 0:
            error = 'Valid quantity is required'
        elif not reason:
            error = 'Reason is required'
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('inventory.stock_out'))
        
        # Get product and validate quantity
        product = Product.query.get_or_404(product_id)
        quantity = int(quantity)
        
        if product.quantity < quantity:
            flash(f'Not enough inventory. Current quantity: {product.quantity}', 'danger')
            return redirect(url_for('inventory.stock_out'))
        
        # Create inventory log
        log = InventoryLog(
            product_id=product.id,
            action_type='out',
            quantity=quantity,
            reason=reason,
            created_by=current_user.id
        )
        
        # Update product quantity
        product.quantity -= quantity
        
        db.session.add(log)
        db.session.commit()
        
        flash(f'Successfully removed {quantity} units of {product.name}', 'success')
        return redirect(url_for('inventory.index'))
    
    # For GET request, show form with product selection
    return render_template('inventory/stock_out.html')

@bp.route('/adjust', methods=['GET', 'POST'])
@login_required
def adjust():
    """Handle inventory adjustments."""
    # Only admins can adjust inventory
    if not current_user.is_admin():
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('inventory.index'))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        new_quantity = request.form.get('new_quantity')
        reason = request.form.get('reason')
        
        # Validate input
        error = None
        if not product_id:
            error = 'Product is required'
        elif not new_quantity or not new_quantity.isdigit():
            error = 'Valid quantity is required'
        elif not reason:
            error = 'Reason is required'
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('inventory.adjust'))
        
        # Get product and calculate adjustment
        product = Product.query.get_or_404(product_id)
        new_quantity = int(new_quantity)
        adjustment = new_quantity - product.quantity
        
        # Create inventory log
        log = InventoryLog(
            product_id=product.id,
            action_type='adjust',
            quantity=adjustment,
            reason=reason,
            created_by=current_user.id
        )
        
        # Update product quantity
        product.quantity = new_quantity
        
        db.session.add(log)
        db.session.commit()
        
        flash(f'Successfully adjusted inventory for {product.name}', 'success')
        return redirect(url_for('inventory.index'))
    
    # For GET request, show form with product selection
    return render_template('inventory/adjust.html')

@bp.route('/history')
@login_required
def history():
    """View inventory history."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Apply filters
    product_id = request.args.get('product_id')
    action_type = request.args.get('action_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = InventoryLog.query
    
    # Apply filters
    if product_id:
        query = query.filter_by(product_id=product_id)
    
    if action_type:
        query = query.filter_by(action_type=action_type)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryLog.created_at >= start_date)
        except ValueError:
            flash('Invalid start date format', 'warning')
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(InventoryLog.created_at <= end_date)
        except ValueError:
            flash('Invalid end date format', 'warning')
    
    # Order by date descending
    logs = query.order_by(InventoryLog.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get products for filter dropdown
    products = Product.query.order_by(Product.name).all()
    
    return render_template('inventory/history.html', 
                          logs=logs, 
                          products=products,
                          action_types=['in', 'out', 'adjust'],
                          selected_product=product_id,
                          selected_action=action_type,
                          start_date=start_date,
                          end_date=end_date)

@bp.route('/get-product', methods=['POST'])
@login_required
def get_product():
    """Get product details by ID or barcode."""
    product_id = request.form.get('product_id')
    barcode = request.form.get('barcode')
    
    if product_id:
        product = Product.query.get(product_id)
    elif barcode:
        product = Product.query.filter_by(barcode=barcode).first()
    else:
        return jsonify({'success': False, 'message': 'Product ID or barcode required'}), 400
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode,
            'quantity': product.quantity,
            'price': product.price_sell,
            'image': product.get_main_image()
        }
    })
