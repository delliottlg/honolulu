# Data Export Guide - Honolulu Glass Leads

## Current Data Status
- **452 total leads** (45 hotels + 407 businesses)
- **420 with emails** (99.7% capture rate)
- **Database**: `honolulu_hotels.db` (SQLite)

## Export Methods

### 1. Via Web Interface (Easiest)
Visit http://localhost:5007 (or your deployed URL)

- **Export All**: Click "Export All" in navigation → Downloads 452 leads
- **Hotels Only**: Go to Hotels page → Export button
- **Businesses Only**: Go to Businesses page → Export button
- **Filtered Export**: Filter by type first, then export

### 2. Direct URL Access
```
# All leads (hotels + businesses)
http://localhost:5007/export/csv?type=all

# Hotels only
http://localhost:5007/export/csv?type=hotels

# Businesses only
http://localhost:5007/export/csv?type=businesses
```

### 3. Command Line Export
```bash
# Export all leads
curl http://localhost:5007/export/csv?type=all -o honolulu_all_leads.csv

# Export hotels only
curl http://localhost:5007/export/csv?type=hotels -o honolulu_hotels.csv

# Export businesses only
curl http://localhost:5007/export/csv?type=businesses -o honolulu_businesses.csv
```

### 4. Direct Database Query
```bash
# Using sqlite3 command
sqlite3 honolulu_hotels.db

# Export all emails
.headers on
.mode csv
.output all_emails.csv
SELECT name, email, phone, website, address FROM hotels WHERE email IS NOT NULL
UNION ALL
SELECT name, email, phone, website, address FROM businesses WHERE email IS NOT NULL;
.quit
```

### 5. Python Script Export
```python
import sqlite3
import csv

conn = sqlite3.connect('honolulu_hotels.db')
c = conn.cursor()

# Get all leads with emails
c.execute("""
    SELECT 'Hotel' as type, name, email, phone, website, address
    FROM hotels WHERE email IS NOT NULL
    UNION ALL
    SELECT business_type, name, email, phone, website, address
    FROM businesses WHERE email IS NOT NULL
""")

with open('export.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Type', 'Name', 'Email', 'Phone', 'Website', 'Address'])
    writer.writerows(c.fetchall())

conn.close()
print("Exported to export.csv")
```

## Export Formats

### CSV Columns
- **Type**: Business category (Hotel, Glass Contractor, etc.)
- **Name**: Business name
- **Email**: Contact email (primary data point!)
- **Phone**: Phone number
- **Website**: Company website
- **Address**: Physical address
- **Specialty**: Business specialty (for businesses table)
- **Rating**: Google rating

## Email Campaign Segmentation

### High-Value Segments
```sql
-- Beachfront hotels (salt spray damage)
SELECT * FROM hotels WHERE beachfront = 1;

-- Glass contractors (partners/competitors)
SELECT * FROM businesses WHERE business_type = 'glass_contractor';

-- Property managers (multiple buildings)
SELECT * FROM businesses WHERE business_type = 'property_management';

-- Large contractors (big projects)
SELECT * FROM businesses WHERE business_type = 'general_contractor';
```

### Email Templates by Segment

#### Hotels
- Subject: "New Hurricane Glass Requirements for Honolulu Hotels"
- Focus: Insurance savings, guest safety, ocean view protection

#### Contractors
- Subject: "Miami-Dade Certified Glass - Contractor Partnership"
- Focus: Become preferred installer, training available

#### Property Managers
- Subject: "Bulk Pricing for Hurricane Glass Upgrades"
- Focus: Portfolio-wide compliance, volume discounts

#### Hospitals/Schools
- Subject: "Safety Glass Compliance for Critical Infrastructure"
- Focus: Life safety, code compliance, liability reduction

## Automated Export Schedule

### Daily Export Script
```bash
#!/bin/bash
# save as daily_export.sh

DATE=$(date +%Y%m%d)
cd /var/www/honolulu

# Export all data
curl http://localhost:5007/export/csv?type=all -o exports/all_leads_$DATE.csv

# Email to Lance
echo "Daily lead export attached" | mail -s "Honolulu Leads $DATE" -a exports/all_leads_$DATE.csv lance@glassstrategies.com
```

### Set up cron job
```bash
crontab -e
# Add: 0 6 * * * /var/www/honolulu/daily_export.sh
```

## Data Sync to Google Sheets

### Manual Upload
1. Export CSV from web interface
2. Open Google Sheets
3. File → Import → Upload CSV
4. Choose "Replace current sheet"

### Automated Sync (using Google API)
```python
# Install: pip install gspread oauth2client
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup credentials
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Open sheet and update
sheet = client.open("Honolulu Leads").sheet1
sheet.clear()
sheet.update([headers] + data_rows)
```

## Backup Strategy

### Local Backup
```bash
# Backup database daily
cp honolulu_hotels.db backups/honolulu_hotels_$(date +%Y%m%d).db

# Keep only last 30 days
find backups -name "*.db" -mtime +30 -delete
```

### Remote Backup
```bash
# Backup to S3
aws s3 cp honolulu_hotels.db s3://glass-strategies-backups/honolulu/

# Or to another server
scp honolulu_hotels.db backup@backup-server:/backups/
```

## Quick Export Commands

```bash
# Get everything right now
curl http://localhost:5007/export/csv?type=all -o all_leads_now.csv

# Count leads by type
sqlite3 honolulu_hotels.db "SELECT business_type, COUNT(*) FROM businesses GROUP BY business_type"

# Get just emails for mail merge
sqlite3 honolulu_hotels.db "SELECT DISTINCT email FROM (SELECT email FROM hotels UNION SELECT email FROM businesses) WHERE email IS NOT NULL" > emails_only.txt
```

## Notes
- Database is portable - just copy the .db file
- CSVs are ready for any email platform (Mailchimp, SendGrid, etc.)
- All exports include only leads WITH email addresses
- Data refreshes with each scraper run