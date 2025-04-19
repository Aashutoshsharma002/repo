from app import db
from flask_login import UserMixin
from datetime import datetime
import json

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='staff')  # 'admin', 'staff', 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_staff(self):
        return self.role == 'staff' or self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    """Product model representing items in the warehouse."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    barcode = db.Column(db.String(64), unique=True)
    category = db.Column(db.String(64))
    size = db.Column(db.String(32))
    color = db.Column(db.String(32))
    gender = db.Column(db.String(32))
    material = db.Column(db.String(64))
    price_cost = db.Column(db.Float)
    price_sell = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan')
    attributes = db.relationship('ProductAttribute', backref='product', cascade='all, delete-orphan')
    inventory_logs = db.relationship('InventoryLog', backref='product', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def get_main_image(self):
        """Get the featured image or the first image."""
        featured = ProductImage.query.filter_by(product_id=self.id, is_featured=True).first()
        if featured:
            return featured.image_url
        
        first = ProductImage.query.filter_by(product_id=self.id).first()
        if first:
            return first.image_url
        
        return None
    
    def get_attribute_value(self, attribute_name):
        """Get the value of a specific attribute."""
        attr_def = AttributeDefinition.query.filter_by(name=attribute_name).first()
        if not attr_def:
            return None
        
        attr = ProductAttribute.query.filter_by(
            product_id=self.id, 
            attribute_id=attr_def.id
        ).first()
        
        if not attr:
            return None
        
        return attr.value

class ProductImage(db.Model):
    """Product image model."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<ProductImage {self.image_url}>'

class AttributeDefinition(db.Model):
    """Custom attribute definition model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    type = db.Column(db.String(32), nullable=False)  # 'text', 'dropdown', 'checkbox'
    options = db.Column(db.Text)  # JSON string for dropdown options
    required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attributes = db.relationship('ProductAttribute', backref='definition', cascade='all, delete-orphan')
    
    def get_options_list(self):
        """Convert JSON options string to Python list."""
        if self.options:
            return json.loads(self.options)
        return []
    
    def __repr__(self):
        return f'<AttributeDefinition {self.name}>'

class ProductAttribute(db.Model):
    """Product attribute value model."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attribute_definition.id'), nullable=False)
    value = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ProductAttribute {self.definition.name}: {self.value}>'

class InventoryLog(db.Model):
    """Inventory movement log model."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    action_type = db.Column(db.String(32), nullable=False)  # 'in', 'out', 'adjust'
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(128))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<InventoryLog {self.action_type} {self.quantity}>'

class Setting(db.Model):
    """System settings model for configuration."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Setting {self.key}>'
