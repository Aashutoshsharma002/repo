import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create and configure the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Load configuration
app.config.from_object(config.Config)

# Initialize extensions with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Create tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    
    # Check if admin user exists and create if not
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created")

# Setup user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Import routes at the end to avoid circular imports
from flask import render_template
from flask_login import login_required

# Register Blueprints
from routes import auth, products, inventory, reports, admin

app.register_blueprint(auth.bp)
app.register_blueprint(products.bp)
app.register_blueprint(inventory.bp)
app.register_blueprint(reports.bp)
app.register_blueprint(admin.bp)

# Default route
@app.route('/')
@login_required
def index():
    """Main dashboard."""
    from models import Product, InventoryLog
    import datetime
    
    # Get product counts
    total_products = Product.query.count()
    low_stock_threshold = 10  # This could come from settings
    low_stock_count = Product.query.filter(Product.quantity <= low_stock_threshold).count()
    out_of_stock_count = Product.query.filter(Product.quantity <= 0).count()
    
    # Get recent inventory activities
    recent_activities = InventoryLog.query.order_by(InventoryLog.created_at.desc()).limit(5).all()
    
    # Get inventory value
    inventory_value = db.session.query(db.func.sum(Product.price_sell * Product.quantity)).scalar() or 0
    
    # Get today's movements
    today = datetime.datetime.now().date()
    today_start = datetime.datetime.combine(today, datetime.time.min)
    today_end = datetime.datetime.combine(today, datetime.time.max)
    
    stock_in_today = db.session.query(db.func.sum(InventoryLog.quantity)).filter(
        InventoryLog.action_type == 'in',
        InventoryLog.created_at.between(today_start, today_end)
    ).scalar() or 0
    
    stock_out_today = db.session.query(db.func.sum(InventoryLog.quantity)).filter(
        InventoryLog.action_type == 'out',
        InventoryLog.created_at.between(today_start, today_end)
    ).scalar() or 0
    
    return render_template('dashboard.html',
                          total_products=total_products,
                          low_stock_count=low_stock_count,
                          out_of_stock_count=out_of_stock_count,
                          recent_activities=recent_activities,
                          inventory_value=inventory_value,
                          stock_in_today=stock_in_today,
                          stock_out_today=stock_out_today)
