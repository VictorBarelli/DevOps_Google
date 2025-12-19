import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-super-secret-key-change-in-production")

# Demo credentials (in production, use a proper database)
DEMO_USERS = {
    "admin@example.com": "admin123",
    "user@example.com": "user123"
}

@app.route('/')
def home():
    """Redirect to dashboard if logged in, otherwise to login page"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and authentication"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email in DEMO_USERS and DEMO_USERS[email] == password:
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid email or password. Please try again."
    
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    """Protected dashboard page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Extract username from email
    username = session['user'].split('@')[0].title()
    return render_template('dashboard.html', username=username)

@app.route('/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/api/status')
def api_status():
    """API endpoint for health checks"""
    return jsonify({
        "message": "Hello from Google Cloud Run!",
        "status": "success",
        "authenticated": 'user' in session
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
