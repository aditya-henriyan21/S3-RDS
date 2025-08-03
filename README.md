# Flask S3 RDS Demo Application

A simple Flask web application demonstrating user authentication with PostgreSQL RDS and file upload to AWS S3.

## Features

- User registration and login
- PostgreSQL RDS database integration
- File upload to AWS S3
- Simple HTML interface (no frontend frameworks)
- CI/CD with GitHub Actions
- EC2 deployment ready

## Prerequisites

- AWS Account
- GitHub Account
- Basic knowledge of AWS services (EC2, RDS, S3)

## AWS Setup Instructions

### 1. Create S3 Bucket

#### Step 1: Create the Bucket
1. Go to AWS Console → S3
2. Click "Create bucket"
3. Choose a unique bucket name (e.g., `your-app-uploads-bucket`)
4. Select your preferred region
5. **Block Public Access**: Keep all public access blocked (recommended for security)
6. Click "Create bucket"

#### Step 2: Configure Bucket Permissions
1. Go to your bucket → Permissions tab
2. **Bucket Policy**: Add this policy (replace `YOUR-BUCKET-NAME`):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAppAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/YOUR-IAM-USER"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

#### Step 3: Create IAM User for S3 Access
1. Go to AWS Console → IAM
2. Click "Users" → "Create user"
3. Username: `flask-app-user`
4. Select "Programmatic access"
5. Attach policy: `AmazonS3FullAccess` (or create custom policy with limited permissions)
6. **Save the Access Key ID and Secret Access Key** - you'll need these!

### 2. Create PostgreSQL RDS Instance

#### Step 1: Create RDS Instance
1. Go to AWS Console → RDS
2. Click "Create database"
3. Choose "PostgreSQL"
4. Template: "Free tier" (for learning/demo)
5. **DB instance identifier**: `flask-demo-db`
6. **Master username**: `postgres`
7. **Master password**: Choose a strong password (save it!)
8. **DB instance class**: `db.t3.micro` (free tier eligible)
9. **Storage**: 20 GB (minimum)
10. **VPC**: Default VPC
11. **Public access**: Yes (for demo purposes)
12. **VPC security group**: Create new → Name: `flask-demo-db-sg`
13. **Database name**: `flaskapp`
14. Click "Create database"

#### Step 2: Configure Security Group
1. Go to EC2 Console → Security Groups
2. Find `flask-demo-db-sg`
3. Edit inbound rules:
   - Type: PostgreSQL
   - Port: 5432
   - Source: Your IP address (for direct access)
   - Source: EC2 security group (for app access)

### 3. Set Up EC2 Instance

#### Step 1: Launch EC2 Instance
1. Go to AWS Console → EC2
2. Click "Launch Instance"
3. **Name**: `flask-demo-server`
4. **AMI**: Ubuntu Server 22.04 LTS
5. **Instance type**: `t2.micro` (free tier)
6. **Key pair**: Create new or use existing
7. **Security group**: Create new
   - SSH (port 22): Your IP
   - HTTP (port 80): Anywhere
   - Custom TCP (port 5000): Anywhere
8. Click "Launch instance"

#### Step 2: Connect to EC2 Instance
```bash
# Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install PostgreSQL client
sudo apt install postgresql-client -y
```

### 4. Install PostgreSQL Client and Connect to RDS

#### Step 1: Test Connection to RDS
```bash
# Replace with your RDS endpoint and credentials
psql -h your-rds-endpoint.region.rds.amazonaws.com -U postgres -d flaskapp

# Example:
# psql -h flask-demo-db.abcdef123456.us-east-1.rds.amazonaws.com -U postgres -d flaskapp
```

#### Step 2: Create Database and Tables
Once connected to PostgreSQL:
```sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    s3_key VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check tables were created
\dt

-- Exit
\q
```

### 5. Deploy Flask App to EC2

#### Step 1: Prepare EC2 for Deployment
```bash
# Connect to EC2 via SSH
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install PostgreSQL client
sudo apt install postgresql-client -y

# Create app directory (GitHub Actions will deploy code here)
mkdir -p /home/ubuntu/flask-app
```

#### Step 2: Setup GitHub Repository and Secrets
1. **Push your code to GitHub**:
```bash
# In your local project directory
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

2. **Configure GitHub Secrets**:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Add these secrets:

   **Deployment Secrets:**
   - `EC2_HOST`: Your EC2 public IP address
   - `EC2_USER`: `ubuntu`
   - `EC2_SSH_KEY`: Your private SSH key content (entire .pem file content)

   **Application Secrets:**
   - `SECRET_KEY`: Your Flask secret key (generate a secure random string)
   - `DB_HOST`: Your RDS endpoint
   - `DB_NAME`: `flaskapp`
   - `DB_USER`: `postgres`
   - `DB_PASSWORD`: Your RDS password
   - `DB_PORT`: `5432`
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `AWS_REGION`: Your AWS region (e.g., `us-east-1`)
   - `S3_BUCKET`: Your S3 bucket name

💡 **Note**: The GitHub Actions workflow will automatically create the `/etc/flask-app.env` file on EC2 using these secrets during deployment. No manual environment setup needed on EC2!

#### Step 3: Automated Deployment
The GitHub Actions workflow will automatically:
1. **On every push to main branch**:
   - Run tests
   - Deploy code to EC2 via SCP
   - Install/update dependencies
   - Create systemd service (first time)
   - Restart the application

**No manual deployment needed** - just push to GitHub!

#### Step 4: Verify Deployment
After pushing to GitHub:
1. Check GitHub Actions tab for deployment status
2. Visit `http://your-ec2-public-ip:5000` to test the app
3. SSH to EC2 to check service status:
```bash
sudo systemctl status flaskapp
sudo journalctl -u flaskapp -f  # View live logs
```

### 6. Environment Variables Reference

All environment variables are managed through **GitHub Secrets** and automatically deployed to EC2.

**No manual environment setup required on EC2!**

**Required GitHub Secrets:**
- `SECRET_KEY`: Flask secret key for sessions
- `DB_HOST`: RDS endpoint
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_PORT`: Database port (usually 5432)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
- `S3_BUCKET`: S3 bucket name

**For Local Development:**
Create a `.env` file in your project root:
```env
SECRET_KEY=your-secret-key-for-local-dev
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_NAME=flaskapp
DB_USER=postgres
DB_PASSWORD=your-rds-password
DB_PORT=5432
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (create `.env` file or export manually)

3. Run the application:
```bash
python app.py
```

4. Visit `http://localhost:5000`

### Local Deployment Testing

For testing the deployment process locally, use the included deployment script:

```bash
# Set environment variables
export EC2_HOST=your-ec2-public-ip
export EC2_USER=ubuntu
export EC2_SSH_KEY_PATH=/path/to/your/key.pem

# Make script executable and run
chmod +x deploy.sh
./deploy.sh
```

This script simulates the GitHub Actions deployment process.

## Testing the Application

1. **Sign Up**: Create a new user account
2. **Login**: Log in with your credentials
3. **Upload File**: Upload a file to S3
4. **Dashboard**: View your uploaded files

## CI/CD with GitHub Actions

The included GitHub Actions workflow automatically deploys your application when you push to the main branch.

### How it Works:
1. **Testing Phase**: Runs syntax checks and unit tests
2. **Deployment Phase**: 
   - Transfers code to EC2 via SCP
   - Sets up virtual environment and dependencies
   - Creates systemd service (first deployment only)
   - Restarts the application service

### Required GitHub Secrets:
Configure these in your GitHub repository (Settings → Secrets and variables → Actions):

**Deployment Secrets:**
- **`EC2_HOST`**: Your EC2 public IP address
- **`EC2_USER`**: `ubuntu` (for Ubuntu EC2 instances)
- **`EC2_SSH_KEY`**: Complete content of your private SSH key (.pem file)

**Application Environment Variables:**
- **`SECRET_KEY`**: Flask secret key (generate a secure random string)
- **`DB_HOST`**: Your RDS endpoint
- **`DB_NAME`**: Database name (`flaskapp`)
- **`DB_USER`**: Database username (`postgres`)
- **`DB_PASSWORD`**: Your RDS password
- **`DB_PORT`**: Database port (`5432`)
- **`AWS_ACCESS_KEY_ID`**: Your AWS access key
- **`AWS_SECRET_ACCESS_KEY`**: Your AWS secret key
- **`AWS_REGION`**: AWS region (e.g., `us-east-1`)
- **`S3_BUCKET`**: Your S3 bucket name

### Deployment Process:
1. **Local Development**: Code and test locally
2. **Push to GitHub**: `git push origin main`
3. **Automatic Deployment**: GitHub Actions handles the rest
4. **Verification**: Check your app at `http://your-ec2-ip:5000`

### Monitoring Deployments:
- **GitHub**: Check the "Actions" tab for deployment status
- **EC2 Logs**: `sudo journalctl -u flaskapp -f`
- **Service Status**: `sudo systemctl status flaskapp`

## Security Notes

⚠️ **This is a demo application. For production use:**

1. Use environment-specific configurations
2. Implement proper error handling
3. Add input validation and sanitization
4. Use HTTPS
5. Implement rate limiting
6. Add logging and monitoring
7. Use IAM roles instead of access keys
8. Implement proper backup strategies
9. Add database connection pooling
10. Use a reverse proxy (nginx)

## Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check RDS security group allows connections
   - Verify RDS endpoint and credentials
   - Ensure RDS is publicly accessible (for demo)

2. **S3 Upload Failed**
   - Verify AWS credentials
   - Check S3 bucket permissions
   - Ensure bucket exists and is in correct region

3. **Application Won't Start**
   - Check environment variables are set
   - Verify all dependencies are installed
   - Check application logs: `sudo journalctl -u flaskapp -f`

4. **Can't Connect to EC2**
   - Verify security group allows SSH (port 22)
   - Check SSH key permissions: `chmod 400 your-key.pem`
   - Ensure you're using correct username (`ubuntu` for Ubuntu AMI)

## Cost Considerations

**Free Tier Resources Used:**
- EC2 t2.micro: 750 hours/month
- RDS db.t3.micro: 750 hours/month
- S3: 5GB storage, 20,000 GET requests, 2,000 PUT requests

**Monitor your usage** to avoid unexpected charges!

## Next Steps

To enhance this application:
1. Add file download functionality
2. Implement file sharing between users
3. Add file type restrictions
4. Implement user profiles
5. Add email verification
6. Implement password reset
7. Add file preview capabilities
8. Implement user roles and permissions