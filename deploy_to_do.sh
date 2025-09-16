#!/bin/bash

# Digital Ocean Deployment Script for Honolulu Hotel Scraper
# Run this on your Digital Ocean droplet after SSH-ing in

echo "=== Glass Strategies Honolulu Deployment ==="

# 1. Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Python and dependencies
echo "Installing Python and pip..."
sudo apt install python3 python3-pip python3-venv nginx -y

# 3. Create app directory
echo "Setting up app directory..."
sudo mkdir -p /var/www/honolulu
sudo chown $USER:$USER /var/www/honolulu
cd /var/www/honolulu

# 4. Clone or copy your code
echo "Copy your files to /var/www/honolulu/"
echo "You can use: scp -r * root@your-droplet-ip:/var/www/honolulu/"
echo "Press Enter when files are copied..."
read

# 5. Set up Python virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 7. Set up environment variables
echo "Setting up environment variables..."
cat > .env << EOF
SERPAPI_KEY=69ba8b9b642039edc041e7259c22bcf76072009bc53150bcbb810b9cbd726a6d
FLASK_APP=app.py
EOF

# 8. Create gunicorn service
echo "Creating systemd service..."
sudo cat > /etc/systemd/system/honolulu.service << EOF
[Unit]
Description=Honolulu Hotel Scraper
After=network.target

[Service]
User=$USER
WorkingDirectory=/var/www/honolulu
Environment="PATH=/var/www/honolulu/venv/bin"
ExecStart=/var/www/honolulu/venv/bin/gunicorn --workers 3 --bind unix:honolulu.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
EOF

# 9. Configure Nginx
echo "Configuring Nginx..."
sudo cat > /etc/nginx/sites-available/honolulu << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/honolulu/honolulu.sock;
    }
}
EOF

# 10. Enable and start services
echo "Starting services..."
sudo ln -s /etc/nginx/sites-available/honolulu /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl start honolulu
sudo systemctl enable honolulu

echo "=== Deployment Complete! ==="
echo "Your app should be running at http://your-droplet-ip"
echo "Check status: sudo systemctl status honolulu"
echo "View logs: sudo journalctl -u honolulu -f"