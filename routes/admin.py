import os
import json
import tempfile
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import User, AttributeDefinition, Setting, Product, ProductAttribute
from utils import parse_excel_import

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
def index():
    """Admin dashboard."""
    # Only admins can access admin panel
    if not current_user.is_admin():
        flash('You do not have permission to access the admin panel', 'danger')
        return redirect(url_for('index'))
    
    # Get system statistics
    total_products = Product.query.count()
    total_users = User.query.count()
    total_attributes = AttributeDefinition.query.count()
    
    return render_template('admin/settings.html', 
                          total_products=total_products,
                          total_users=total_users, 
                          total_attributes=total_attributes)

@bp.route('/users')
@login_required
def users():
    """Manage users."""
    # Only admins can manage users
    if not current_user.is_admin():
        flash('You do not have permission to manage users', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user."""
    # Only admins can delete users
    if not current_user.is_admin():
        flash('You do not have permission to delete users', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent deleting self
    if user_id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted successfully', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/attributes', methods=['GET', 'POST'])
@login_required
def attributes():
    """Manage product attributes."""
    # Only admins can manage attributes
    if not current_user.is_admin():
        flash('You do not have permission to manage attributes', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        attr_type = request.form.get('type')
        options = request.form.get('options')
        required = True if request.form.get('required') == 'on' else False
        
        # Validate input
        if not name or not attr_type:
            flash('Name and type are required', 'danger')
            return redirect(url_for('admin.attributes'))
        
        # Check if attribute already exists
        if AttributeDefinition.query.filter_by(name=name).first():
            flash('Attribute with this name already exists', 'danger')
            return redirect(url_for('admin.attributes'))
        
        # Process options for dropdown type
        options_json = None
        if attr_type == 'dropdown' and options:
            try:
                # Split by commas and strip whitespace
                options_list = [opt.strip() for opt in options.split(',') if opt.strip()]
                options_json = json.dumps(options_list)
            except Exception as e:
                current_app.logger.error(f"Options parsing error: {e}")
                flash('Invalid options format', 'danger')
                return redirect(url_for('admin.attributes'))
        
        # Create new attribute
        new_attr = AttributeDefinition(
            name=name,
            type=attr_type,
            options=options_json,
            required=required
        )
        
        db.session.add(new_attr)
        db.session.commit()
        
        flash('Attribute added successfully', 'success')
        return redirect(url_for('admin.attributes'))
    
    # Get all attributes
    attributes = AttributeDefinition.query.all()
    return render_template('admin/attributes.html', attributes=attributes)

@bp.route('/edit-attribute/<int:attr_id>', methods=['GET', 'POST'])
@login_required
def edit_attribute(attr_id):
    """Edit an attribute definition."""
    # Only admins can edit attributes
    if not current_user.is_admin():
        flash('You do not have permission to edit attributes', 'danger')
        return redirect(url_for('admin.attributes'))
    
    attr = AttributeDefinition.query.get_or_404(attr_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        options = request.form.get('options')
        required = True if request.form.get('required') == 'on' else False
        
        # Validate input
        if not name:
            flash('Name is required', 'danger')
            return redirect(url_for('admin.edit_attribute', attr_id=attr.id))
        
        # Check if name changed and already exists
        if name != attr.name and AttributeDefinition.query.filter_by(name=name).first():
            flash('Attribute with this name already exists', 'danger')
            return redirect(url_for('admin.edit_attribute', attr_id=attr.id))
        
        # Update attribute
        attr.name = name
        attr.required = required
        
        # Process options for dropdown type
        if attr.type == 'dropdown' and options:
            try:
                # Split by commas and strip whitespace
                options_list = [opt.strip() for opt in options.split(',') if opt.strip()]
                attr.options = json.dumps(options_list)
            except Exception as e:
                current_app.logger.error(f"Options parsing error: {e}")
                flash('Invalid options format', 'danger')
                return redirect(url_for('admin.edit_attribute', attr_id=attr.id))
        
        db.session.commit()
        
        flash('Attribute updated successfully', 'success')
        return redirect(url_for('admin.attributes'))
    
    # Parse options for display
    options_str = ""
    if attr.options:
        try:
            options_list = json.loads(attr.options)
            options_str = ", ".join(options_list)
        except:
            pass
    
    return render_template('admin/edit_attribute.html', attribute=attr, options_str=options_str)

@bp.route('/delete-attribute/<int:attr_id>', methods=['POST'])
@login_required
def delete_attribute(attr_id):
    """Delete an attribute definition."""
    # Only admins can delete attributes
    if not current_user.is_admin():
        flash('You do not have permission to delete attributes', 'danger')
        return redirect(url_for('admin.attributes'))
    
    attr = AttributeDefinition.query.get_or_404(attr_id)
    
    # Check if attribute is in use
    attr_count = ProductAttribute.query.filter_by(attribute_id=attr.id).count()
    if attr_count > 0:
        flash(f'Cannot delete attribute that is used by {attr_count} products', 'danger')
        return redirect(url_for('admin.attributes'))
    
    db.session.delete(attr)
    db.session.commit()
    
    flash('Attribute deleted successfully', 'success')
    return redirect(url_for('admin.attributes'))

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Manage system settings."""
    # Only admins can manage settings
    if not current_user.is_admin():
        flash('You do not have permission to manage settings', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        barcode_type = request.form.get('barcode_type', 'code128')
        
        # Update settings
        update_setting('barcode_type', barcode_type)
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    # Get current settings
    barcode_type = get_setting('barcode_type', 'code128')
    
    return render_template('admin/settings.html', barcode_type=barcode_type)

@bp.route('/import-export', methods=['GET', 'POST'])
@login_required
def import_export():
    """Import and export products."""
    # Only admins can import/export
    if not current_user.is_admin():
        flash('You do not have permission to import/export products', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'import':
            # Handle import
            if 'excel_file' not in request.files:
                flash('No file selected', 'danger')
                return redirect(url_for('admin.import_export'))
            
            file = request.files['excel_file']
            
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(url_for('admin.import_export'))
            
            if not file.filename.endswith(('.xlsx', '.xls')):
                flash('Invalid file format. Please upload an Excel file (.xlsx, .xls)', 'danger')
                return redirect(url_for('admin.import_export'))
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp:
                file.save(temp.name)
                temp_path = temp.name
            
            # Parse Excel file
            products_data = parse_excel_import(temp_path)
            
            # Delete temporary file
            os.unlink(temp_path)
            
            if not products_data:
                flash('Failed to parse Excel file or no valid products found', 'danger')
                return redirect(url_for('admin.import_export'))
            
            # Process products
            imported_count = 0
            updated_count = 0
            error_count = 0
            
            for product_data in products_data:
                try:
                    # Check if product exists
                    product = Product.query.filter_by(sku=product_data['sku']).first()
                    
                    if product:
                        # Update existing product
                        product.name = product_data['name']
                        product.barcode = product_data['barcode']
                        product.category = product_data['category']
                        product.size = product_data['size']
                        product.color = product_data['color']
                        product.gender = product_data['gender']
                        product.material = product_data['material']
                        product.price_cost = product_data['price_cost']
                        product.price_sell = product_data['price_sell']
                        product.quantity = product_data['quantity']
                        product.location = product_data['location']
                        
                        updated_count += 1
                    else:
                        # Create new product
                        product = Product(
                            sku=product_data['sku'],
                            name=product_data['name'],
                            barcode=product_data['barcode'],
                            category=product_data['category'],
                            size=product_data['size'],
                            color=product_data['color'],
                            gender=product_data['gender'],
                            material=product_data['material'],
                            price_cost=product_data['price_cost'],
                            price_sell=product_data['price_sell'],
                            quantity=product_data['quantity'],
                            location=product_data['location']
                        )
                        
                        db.session.add(product)
                        db.session.flush()  # Get product ID without committing
                        
                        imported_count += 1
                    
                    # Process dynamic attributes
                    for attr_name, attr_value in product_data['attributes'].items():
                        # Find or create attribute definition
                        attr_def = AttributeDefinition.query.filter_by(name=attr_name).first()
                        
                        if not attr_def:
                            # Create new attribute definition
                            attr_def = AttributeDefinition(
                                name=attr_name,
                                type='text',
                                required=False
                            )
                            db.session.add(attr_def)
                            db.session.flush()  # Get attribute ID without committing
                        
                        # Find existing attribute value
                        attr = ProductAttribute.query.filter_by(
                            product_id=product.id,
                            attribute_id=attr_def.id
                        ).first()
                        
                        if attr:
                            # Update existing attribute
                            attr.value = attr_value
                        else:
                            # Create new attribute value
                            attr = ProductAttribute(
                                product_id=product.id,
                                attribute_id=attr_def.id,
                                value=attr_value
                            )
                            db.session.add(attr)
                    
                except Exception as e:
                    current_app.logger.error(f"Import error for SKU {product_data['sku']}: {e}")
                    error_count += 1
            
            db.session.commit()
            
            flash(f'Import complete. Imported: {imported_count}, Updated: {updated_count}, Errors: {error_count}', 'success')
            return redirect(url_for('admin.import_export'))
    
    return render_template('admin/import_export.html')

def get_setting(key, default=None):
    """Get a setting value from the database."""
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        return setting.value
    return default

def update_setting(key, value):
    """Update or create a setting in the database."""
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    
    db.session.commit()
