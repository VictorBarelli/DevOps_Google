"""
Unit Tests for GCP DevOps Dashboard
Run with: pytest tests/ -v
"""

import pytest
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app, db, User


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test user
            test_user = User(name='Test User', email='test@test.com')
            test_user.set_password('password123')
            db.session.add(test_user)
            
            # Create an admin user
            admin_user = User(name='Admin', email='admin@test.com', is_admin=True)
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            db.session.commit()
        yield client


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    client.post('/login', data={
        'email': 'test@test.com',
        'password': 'password123'
    })
    return client


@pytest.fixture
def admin_client(client):
    """Create an authenticated admin test client."""
    client.post('/login', data={
        'email': 'admin@test.com',
        'password': 'admin123'
    })
    return client


class TestHomePage:
    """Tests for the home page."""
    
    def test_home_redirects_to_login(self, client):
        """Test that home page redirects to login when not authenticated."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_home_redirects_to_dashboard_when_authenticated(self, authenticated_client):
        """Test that home redirects to dashboard when authenticated."""
        response = authenticated_client.get('/')
        assert response.status_code == 302
        assert '/dashboard' in response.location


class TestLoginPage:
    """Tests for the login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Sign in' in response.data or b'Login' in response.data
    
    def test_login_with_valid_credentials(self, client):
        """Test login with valid credentials."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome' in response.data or b'Dashboard' in response.data
    
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'error' in response.data.lower()
    
    def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', data={
            'email': 'nonexistent@test.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'Invalid' in response.data


class TestRegistrationPage:
    """Tests for the registration functionality."""
    
    def test_register_page_loads(self, client):
        """Test that registration page loads successfully."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Create' in response.data or b'Register' in response.data
    
    def test_register_new_user(self, client):
        """Test registering a new user."""
        response = client.post('/register', data={
            'name': 'New User',
            'email': 'newuser@test.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify user was created
        with app.app_context():
            user = User.query.filter_by(email='newuser@test.com').first()
            assert user is not None
            assert user.name == 'New User'
    
    def test_register_with_existing_email(self, client):
        """Test registration with existing email."""
        response = client.post('/register', data={
            'name': 'Another User',
            'email': 'test@test.com',  # Already exists
            'password': 'password123',
            'confirm_password': 'password123'
        })
        assert response.status_code == 200
        assert b'already exists' in response.data.lower() or b'error' in response.data.lower()
    
    def test_register_with_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/register', data={
            'name': 'Test User',
            'email': 'mismatch@test.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        })
        assert response.status_code == 200
        assert b'match' in response.data.lower() or b'error' in response.data.lower()


class TestDashboard:
    """Tests for the dashboard functionality."""
    
    def test_dashboard_requires_authentication(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_dashboard_loads_when_authenticated(self, authenticated_client):
        """Test that dashboard loads for authenticated users."""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Welcome' in response.data or b'Dashboard' in response.data


class TestAdminPanel:
    """Tests for the admin panel functionality."""
    
    def test_admin_page_requires_authentication(self, client):
        """Test that admin page requires authentication."""
        response = client.get('/admin/users')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_admin_page_requires_admin_role(self, authenticated_client):
        """Test that admin page requires admin role."""
        response = authenticated_client.get('/admin/users')
        assert response.status_code == 302
        assert '/dashboard' in response.location
    
    def test_admin_page_loads_for_admin(self, admin_client):
        """Test that admin page loads for admin users."""
        response = admin_client.get('/admin/users')
        assert response.status_code == 200
        assert b'User' in response.data


class TestLogout:
    """Tests for logout functionality."""
    
    def test_logout(self, authenticated_client):
        """Test that logout works correctly."""
        response = authenticated_client.post('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify user is logged out
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.location


class TestAPIEndpoints:
    """Tests for API endpoints."""
    
    def test_api_status_endpoint(self, client):
        """Test the API status endpoint."""
        response = client.get('/api/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'success'
    
    def test_api_users_requires_auth(self, client):
        """Test that API users endpoint requires authentication."""
        response = client.get('/api/users')
        assert response.status_code == 401
    
    def test_api_users_for_authenticated(self, authenticated_client):
        """Test API users endpoint for authenticated users."""
        response = authenticated_client.get('/api/users')
        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data


class TestUserModel:
    """Tests for the User model."""
    
    def test_password_hashing(self, client):
        """Test that passwords are properly hashed."""
        with app.app_context():
            user = User(name='Hash Test', email='hash@test.com')
            user.set_password('testpassword')
            
            # Password should be hashed, not plain text
            assert user.password_hash != 'testpassword'
            
            # Check password should work
            assert user.check_password('testpassword') is True
            assert user.check_password('wrongpassword') is False
    
    def test_user_repr(self, client):
        """Test User string representation."""
        with app.app_context():
            user = User(name='Test', email='repr@test.com')
            assert 'repr@test.com' in repr(user)
