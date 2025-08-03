import unittest
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        """Test home page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to Flask S3 RDS Demo', response.data)

    def test_signup_page(self):
        """Test signup page loads"""
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Your Account', response.data)

    def test_login_page(self):
        """Test login page loads"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login to Your Account', response.data)

    def test_dashboard_redirect_when_not_logged_in(self):
        """Test dashboard redirects to login when not authenticated"""
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login to Your Account', response.data)

    def test_upload_redirect_when_not_logged_in(self):
        """Test upload redirects to login when not authenticated"""
        response = self.app.get('/upload', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login to Your Account', response.data)

if __name__ == '__main__':
    unittest.main()