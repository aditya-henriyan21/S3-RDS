import os
import boto3
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Database configuration
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', '5432')

# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS uploads (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    filename VARCHAR(255) NOT NULL,
                    s3_key VARCHAR(255) NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            conn.commit()
            cur.close()
            conn.close()
            print("Database tables initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if not username or not email or not password:
            flash('All fields are required!')
            return render_template('signup.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                
                # Check if user already exists
                cur.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
                if cur.fetchone():
                    flash('Username or email already exists!')
                    return render_template('signup.html')
                
                # Create new user
                password_hash = generate_password_hash(password)
                cur.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                    (username, email, password_hash)
                )
                conn.commit()
                cur.close()
                conn.close()
                
                flash('Registration successful! Please login.')
                return redirect(url_for('login'))
                
            except Exception as e:
                flash(f'Registration failed: {e}')
                return render_template('signup.html')
        else:
            flash('Database connection failed!')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT id, password_hash FROM users WHERE username = %s', (username,))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user and check_password_hash(user[1], password):
                    session['user_id'] = user[0]
                    session['username'] = username
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!')
            except Exception as e:
                flash(f'Login failed: {e}')
        else:
            flash('Database connection failed!')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's uploaded files
    conn = get_db_connection()
    uploads = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT filename, upload_date FROM uploads WHERE user_id = %s ORDER BY upload_date DESC',
                (session['user_id'],)
            )
            uploads = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            flash(f'Error fetching uploads: {e}')
    
    return render_template('dashboard.html', uploads=uploads)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """File upload to S3"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!')
            return render_template('upload.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!')
            return render_template('upload.html')
        
        if file:
            try:
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                # Upload to S3
                s3_client.upload_fileobj(
                    file,
                    S3_BUCKET,
                    unique_filename,
                    ExtraArgs={'ACL': 'private'}
                )
                
                # Save to database
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute(
                        'INSERT INTO uploads (user_id, filename, s3_key) VALUES (%s, %s, %s)',
                        (session['user_id'], filename, unique_filename)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                
                flash('File uploaded successfully!')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                flash(f'Upload failed: {e}')
    
    return render_template('upload.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)