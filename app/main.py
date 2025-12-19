import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-super-secret-key-change-in-production")

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "users.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

# Create tables and default admin
def create_default_admin():
    """Create default admin account if it doesn't exist"""
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@admin.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            name='Administrator',
            email=admin_email,
            is_admin=True,
            is_active=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"Default admin created: {admin_email}")

with app.app_context():
    db.create_all()
    create_default_admin()

@app.route('/')
def home():
    """Redirect to dashboard if logged in, otherwise to login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and authentication"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid email or password. Please try again."
    
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    error = None
    success = None
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not name or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif User.query.filter_by(email=email).first():
            error = "An account with this email already exists."
        else:
            # Create new user
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            success = "Account created successfully! You can now sign in."
            return render_template('login.html', success=success)
    
    return render_template('register.html', error=error, success=success)

@app.route('/dashboard')
def dashboard():
    """Protected dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = session.get('user_name', 'User')
    return render_template('dashboard.html', username=username)

@app.route('/admin/users')
def admin_users():
    """Admin page to view all users - Admin only"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is admin
    if not session.get('is_admin', False):
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    total_users = len(users)
    
    # Calculate stats
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    active_today = User.query.filter(
        User.last_login >= datetime.combine(today, datetime.min.time())
    ).count()
    
    new_this_week = User.query.filter(User.created_at >= week_ago).count()
    
    return render_template('admin.html', 
                          users=users, 
                          total_users=total_users,
                          active_today=active_today,
                          new_this_week=new_this_week)

@app.route('/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/status')
def api_status():
    """API endpoint for health checks"""
    return jsonify({
        "message": "Hello from Google Cloud Run!",
        "status": "success",
        "authenticated": 'user_id' in session
    })

@app.route('/api/users')
def api_users():
    """API endpoint to get all users (for debugging)"""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    users = User.query.all()
    return jsonify({
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ]
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
