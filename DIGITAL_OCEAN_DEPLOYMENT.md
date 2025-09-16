# Digital Ocean Deployment Instructions

## Prerequisites
- Digital Ocean account
- Droplet (Ubuntu 22.04 recommended, $6/month basic is fine)
- Domain name (optional)

## Step 1: Create Droplet
1. Log into Digital Ocean
2. Create Droplet → Ubuntu 22.04 → Basic → $6/month
3. Choose datacenter closest to Hawaii (San Francisco)
4. Add SSH key or use password
5. Name it: `honolulu-glass-leads`

## Step 2: SSH into Droplet
```bash
ssh root@your-droplet-ip
```

## Step 3: Clone and Setup
```bash
# Update system
apt update && apt upgrade -y

# Install Python and required packages
apt install python3 python3-pip python3-venv nginx git -y

# Clone the repository
cd /var/www
git clone https://github.com/delliottlg/honolulu.git
cd honolulu

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create logs directory
mkdir -p /var/log/gunicorn
```

## Step 4: Configure Gunicorn Service
```bash
# Create service file
cat > /etc/systemd/system/honolulu.service << 'EOF'
[Unit]
Description=Honolulu Glass Lead Generator
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/honolulu
Environment="PATH=/var/www/honolulu/venv/bin"
ExecStart=/var/www/honolulu/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5007 app:app

Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
systemctl start honolulu
systemctl enable honolulu
systemctl status honolulu
```

## Step 5: Configure Nginx (Optional - for domain)
```bash
# Create Nginx config
cat > /etc/nginx/sites-available/honolulu << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Change this!

    location / {
        proxy_pass http://127.0.0.1:5007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/honolulu /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx
```

## Step 6: Configure Firewall
```bash
ufw allow 22
ufw allow 80
ufw allow 5007
ufw enable
```

## Step 7: Access Your App
- Direct: `http://your-droplet-ip:5007`
- With domain: `http://your-domain.com`

## Managing the App

### View logs
```bash
journalctl -u honolulu -f
```

### Restart app
```bash
systemctl restart honolulu
```

### Update code
```bash
cd /var/www/honolulu
git pull
systemctl restart honolulu
```

### Run scraper manually
```bash
cd /var/www/honolulu
source venv/bin/activate
python test_comprehensive.py
```

## Data Management

### Download database from server
```bash
# From your local machine
scp root@your-droplet-ip:/var/www/honolulu/honolulu_hotels.db ./
```

### Export CSVs from server
```bash
# SSH into server
ssh root@your-droplet-ip

# Generate exports
cd /var/www/honolulu
source venv/bin/activate

# Export all leads
curl http://localhost:5007/export/csv?type=all -o all_leads.csv

# Download to local machine (from your computer)
scp root@your-droplet-ip:/var/www/honolulu/all_leads.csv ./
```

## Automated Daily Scraping (Optional)

### Set up cron job
```bash
# Edit crontab
crontab -e

# Add this line to run at 2 AM daily
0 2 * * * cd /var/www/honolulu && /var/www/honolulu/venv/bin/python test_comprehensive.py >> /var/log/scraper.log 2>&1
```

## Security Notes

⚠️ **IMPORTANT**: The API key is currently hardcoded in app.py. For production:

1. Create environment file:
```bash
echo "SERPAPI_KEY=your_key_here" > /var/www/honolulu/.env
```

2. Update app.py to read from environment:
```python
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('SERPAPI_KEY')
```

## Troubleshooting

### App not starting?
```bash
systemctl status honolulu
journalctl -u honolulu -n 50
```

### Database locked?
```bash
systemctl stop honolulu
rm /var/www/honolulu/honolulu_hotels.db-journal
systemctl start honolulu
```

### Out of memory?
Consider upgrading to $12/month droplet with 2GB RAM

## Quick Start Commands
```bash
# Complete setup in one go
ssh root@your-droplet-ip
apt update && apt upgrade -y && apt install python3 python3-pip python3-venv nginx git -y && cd /var/www && git clone https://github.com/delliottlg/honolulu.git && cd honolulu && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && mkdir -p /var/log/gunicorn
```

Then create the service file and you're done!