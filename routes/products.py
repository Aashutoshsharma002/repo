import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import Product, ProductImage, AttributeDefinition, ProductAttribute
from utils import generate_sku, save_barcode_image, save_image

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/')
@login_required
def list():
    """List all products."""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PER_PAGE']
    
    # Get filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    # Base query
    query = Product.query
    
    # Apply filters
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | 
                            Product.sku.ilike(f'%{search}%') |
                            Product.barcode.ilike(f'%{search}%'))
    
    if category:
        query = query.filter_by(category=category)
    
    # Get distinct categories for filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    # Paginate results
    products = query.order_by(Product.name).paginate(page=page, per_page=per_page)
    
    return render_template('product/list.html', 
                          products=products, 
                          search=search, 
                          category=category,
                          categories=categories)

@bp.route('/view/<int:product_id>')
@login_required
def view(product_id):
    """View product details."""
    product = Product.query.get_or_404(product_id)
    
    # Get all attributes
    attributes = []
    for attr in product.attributes:
        definition = AttributeDefinition.query.get(attr.attribute_id)
        attributes.append({
            'name': definition.name,
            'value': attr.value,
            'type': definition.type
        })
    
    return render_template('product/view.html', product=product, attributes=attributes)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new product."""
    # Only admins and staff can add products
    if not current_user.is_staff():
        flash('You do not have permission to add products', 'danger')
        return redirect(url_for('products.list'))
    
    # Get all attribute definitions
    attribute_defs = AttributeDefinition.query.all()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        sku = request.form.get('sku') or generate_sku()
        barcode = request.form.get('barcode')
        category = request.form.get('category')
        size = request.form.get('size')
        color = request.form.get('color')
        gender = request.form.get('gender')
        material = request.form.get('material')
        price_cost = request.form.get('price_cost')
        price_sell = request.form.get('price_sell')
        quantity = request.form.get('quantity', 0)
        location = request.form.get('location')
        
        # Validate required fields
        if not name:
            flash('Product name is required', 'danger')
            return render_template('product/add.html', attribute_defs=attribute_defs)
        
        # Check if SKU already exists
        if Product.query.filter_by(sku=sku).first():
            flash('SKU already exists', 'danger')
            return render_template('product/add.html', attribute_defs=attribute_defs)
        
        # Handle barcode image upload
        barcode_path = None
        barcode_file = request.files.get('barcode_image')
        if barcode_file and barcode_file.filename:
            barcode_path = save_barcode_image(barcode_file)
            # Store the barcode image path if needed
        
        # Create new product
        new_product = Product(
            name=name,
            sku=sku,
            barcode=barcode,
            category=category,
            size=size,
            color=color,
            gender=gender,
            material=material,
            price_cost=float(price_cost) if price_cost else 0,
            price_sell=float(price_sell) if price_sell else 0,
            quantity=int(quantity) if quantity else 0,
            location=location
        )
        
        db.session.add(new_product)
        db.session.flush()  # Get product ID without committing
        
        # Save product images
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                image_path = save_image(image)
                if image_path:
                    # First image is featured by default
                    is_featured = len(new_product.images) == 0
                    product_image = ProductImage(
                        product_id=new_product.id,
                        image_url=image_path,
                        is_featured=is_featured
                    )
                    db.session.add(product_image)
        
        # Save product attributes
        for attr_def in attribute_defs:
            value = request.form.get(f'attribute_{attr_def.id}')
            if value:
                attr = ProductAttribute(
                    product_id=new_product.id,
                    attribute_id=attr_def.id,
                    value=value
                )
                db.session.add(attr)
        
        db.session.commit()
        flash('Product added successfully', 'success')
        return redirect(url_for('products.view', product_id=new_product.id))
    
    return render_template('product/add.html', attribute_defs=attribute_defs)

@bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit(product_id):
    """Edit product details."""
    # Only admins and staff can edit products
    if not current_user.is_staff():
        flash('You do not have permission to edit products', 'danger')
        return redirect(url_for('products.list'))
    
    product = Product.query.get_or_404(product_id)
    attribute_defs = AttributeDefinition.query.all()
    
    if request.method == 'POST':
        # Update product data
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.size = request.form.get('size')
        product.color = request.form.get('color')
        product.gender = request.form.get('gender')
        product.material = request.form.get('material')
        product.price_cost = float(request.form.get('price_cost', 0))
        product.price_sell = float(request.form.get('price_sell', 0))
        product.location = request.form.get('location')
        
        # Update barcode if changed
        new_barcode = request.form.get('barcode')
        if new_barcode and new_barcode != product.barcode:
            product.barcode = new_barcode
            
        # Handle barcode image upload
        barcode_file = request.files.get('barcode_image')
        if barcode_file and barcode_file.filename:
            barcode_path = save_barcode_image(barcode_file)
            # For now, we're not storing the barcode image path separately
        
        # Handle new images
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                image_path = save_image(image)
                if image_path:
                    # If no featured image exists, make this one featured
                    is_featured = not ProductImage.query.filter_by(
                        product_id=product.id, is_featured=True
                    ).first()
                    
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=image_path,
                        is_featured=is_featured
                    )
                    db.session.add(product_image)
        
        # Update attributes
        for attr_def in attribute_defs:
            value = request.form.get(f'attribute_{attr_def.id}')
            
            # Find existing attribute
            attr = ProductAttribute.query.filter_by(
                product_id=product.id,
                attribute_id=attr_def.id
            ).first()
            
            if attr:
                # Update existing attribute
                if value:
                    attr.value = value
                else:
                    # Delete if value is empty
                    db.session.delete(attr)
            elif value:
                # Create new attribute
                attr = ProductAttribute(
                    product_id=product.id,
                    attribute_id=attr_def.id,
                    value=value
                )
                db.session.add(attr)
        
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('products.view', product_id=product.id))
    
    # Get current attribute values
    attributes = {}
    for attr in product.attributes:
        attributes[attr.attribute_id] = attr.value
    
    return render_template('product/edit.html', 
                          product=product, 
                          attribute_defs=attribute_defs,
                          attributes=attributes)

@bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete(product_id):
    """Delete a product."""
    # Only admins can delete products
    if not current_user.is_admin():
        flash('You do not have permission to delete products', 'danger')
        return redirect(url_for('products.list'))
    
    product = Product.query.get_or_404(product_id)
    
    # Delete product images from filesystem
    for image in product.images:
        try:
            file_path = os.path.join(current_app.root_path, image.image_url)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting image: {e}")
    
    # Delete product from database (cascade will delete related records)
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('products.list'))

@bp.route('/set-featured-image/<int:image_id>', methods=['POST'])
@login_required
def set_featured_image(image_id):
    """Set an image as the featured image for a product."""
    # Only admins and staff can change featured image
    if not current_user.is_staff():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    image = ProductImage.query.get_or_404(image_id)
    product_id = image.product_id
    
    # Clear featured flag on all images for this product
    ProductImage.query.filter_by(product_id=product_id).update({'is_featured': False})
    
    # Set this image as featured
    image.is_featured = True
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/delete-image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """Delete a product image."""
    # Only admins and staff can delete images
    if not current_user.is_staff():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    image = ProductImage.query.get_or_404(image_id)
    
    # Check if it's the last image
    image_count = ProductImage.query.filter_by(product_id=image.product_id).count()
    if image_count <= 1:
        return jsonify({'success': False, 'message': 'Cannot delete the last image'}), 400
    
    # Check if it's the featured image
    if image.is_featured:
        # Find another image to make featured
        another_image = ProductImage.query.filter_by(
            product_id=image.product_id
        ).filter(
            ProductImage.id != image.id
        ).first()
        
        if another_image:
            another_image.is_featured = True
    
    # Delete file from filesystem
    try:
        file_path = os.path.join(current_app.root_path, image.image_url)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting image file: {e}")
    
    # Delete from database
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/search-by-barcode', methods=['POST'])
@login_required
def search_by_barcode():
    """Search for a product by barcode."""
    barcode = request.form.get('barcode')
    
    if not barcode:
        return jsonify({'success': False, 'message': 'Barcode is required'}), 400
    
    product = Product.query.filter_by(barcode=barcode).first()
    
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
            'image': product.get_main_image(),
            'url': url_for('products.view', product_id=product.id)
        }
    })
