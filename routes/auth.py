from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('auth/login.html')
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Login user
            login_user(user)
            flash('Login successful', 'success')
            
            # Redirect to the page user wanted to access or default to home
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Handle user registration (admin only)."""
    # Only admins can register new users
    if not current_user.is_admin():
        flash('You do not have permission to register new users', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'staff')
        
        # Validate input
        error = None
        
        if not username:
            error = 'Username is required'
        elif not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists'
        elif User.query.filter_by(email=email).first():
            error = 'Email already exists'
        
        if error:
            flash(error, 'danger')
        else:
            # Create new user
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User {username} created successfully', 'success')
            return redirect(url_for('admin.users'))
    
    return render_template('auth/register.html')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle user profile editing."""
    if request.method == 'POST':
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Update email if provided
        if email and email != current_user.email:
            # Check if email is already in use
            if User.query.filter_by(email=email).first():
                flash('Email already in use', 'danger')
            else:
                current_user.email = email
                db.session.commit()
                flash('Email updated successfully', 'success')
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            # Verify current password
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            else:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Password updated successfully', 'success')
        
    return render_template('auth/profile.html')
