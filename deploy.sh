#!/bin/bash

# Local deployment script for testing
# This script simulates what GitHub Actions does

echo "🚀 Starting local deployment simulation..."

# Check if required environment variables are set
if [ -z "$EC2_HOST" ] || [ -z "$EC2_USER" ] || [ -z "$EC2_SSH_KEY_PATH" ]; then
    echo "❌ Error: Please set the following environment variables:"
    echo "   EC2_HOST=your-ec2-public-ip"
    echo "   EC2_USER=ubuntu"
    echo "   EC2_SSH_KEY_PATH=/path/to/your/key.pem"
    exit 1
fi

echo "📦 Copying files to EC2..."
rsync -avz --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude '.env' \
    ./ ${EC2_USER}@${EC2_HOST}:/home/ubuntu/flask-app/

echo "🔧 Setting up application on EC2..."
ssh -i ${EC2_SSH_KEY_PATH} ${EC2_USER}@${EC2_HOST} << 'EOF'
cd /home/ubuntu/flask-app

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service file if it doesn't exist
if [ ! -f "/etc/systemd/system/flaskapp.service" ]; then
    echo "Creating systemd service..."
    sudo tee /etc/systemd/system/flaskapp.service > /dev/null <<EOL
[Unit]
Description=Flask Demo App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/flask-app
Environment=PATH=/home/ubuntu/flask-app/venv/bin
EnvironmentFile=/etc/environment
ExecStart=/home/ubuntu/flask-app/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL
    
    sudo systemctl daemon-reload
    sudo systemctl enable flaskapp
fi

# Restart the application service
sudo systemctl restart flaskapp

# Wait a moment for service to start
sleep 3

# Check if service is running
if sudo systemctl is-active --quiet flaskapp; then
    echo "✅ Deployment successful! Service is running."
else
    echo "❌ Deployment failed - service not running"
    sudo systemctl status flaskapp --no-pager
    exit 1
fi

echo "Service status:"
sudo systemctl status flaskapp --no-pager -l
EOF

echo "🎉 Deployment completed!"
echo "🌐 Your app should be available at: http://${EC2_HOST}:5000"