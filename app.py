from flask import Flask, render_template, jsonify, send_file, request
import sqlite3
import csv
import io
from datetime import datetime
import os
from scraper import scrape_hotels
from honolulu_scraper import scrape_honolulu_glass_industry

app = Flask(__name__)
app.config['SECRET_KEY'] = 'glass-strategies-honolulu-2024'

DATABASE = 'honolulu_hotels.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hotels
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  address TEXT,
                  city TEXT DEFAULT 'Honolulu',
                  state TEXT DEFAULT 'HI',
                  zip_code TEXT,
                  phone TEXT,
                  email TEXT,
                  website TEXT,
                  property_type TEXT,
                  floors INTEGER,
                  rooms INTEGER,
                  beachfront BOOLEAN,
                  star_rating REAL,
                  last_renovation TEXT,
                  decision_maker TEXT,
                  notes TEXT,
                  date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/leads')
def leads():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM hotels ORDER BY date_added DESC')
    hotels = c.fetchall()
    conn.close()
    return render_template('leads.html', hotels=hotels)

@app.route('/businesses')
def businesses():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get filter parameter
    business_type = request.args.get('type', 'all')

    if business_type == 'all':
        c.execute('SELECT * FROM businesses ORDER BY business_type, name')
    else:
        c.execute('SELECT * FROM businesses WHERE business_type = ? ORDER BY name', (business_type,))

    businesses = c.fetchall()

    # Get business type counts
    c.execute('''SELECT business_type, COUNT(*) as count, COUNT(email) as with_email
                 FROM businesses GROUP BY business_type ORDER BY count DESC''')
    type_stats = c.fetchall()

    conn.close()
    return render_template('businesses.html', businesses=businesses, type_stats=type_stats, current_type=business_type)

@app.route('/api/hotels')
def api_hotels():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM hotels')
    hotels = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(hotels)

@app.route('/export/csv')
def export_csv():
    export_type = request.args.get('type', 'hotels')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if export_type == 'all':
        # Export everything - hotels + businesses
        c.execute('''
            SELECT 'Hotel' as type, name, email, phone, website, address, NULL as specialty, star_rating as rating
            FROM hotels WHERE email IS NOT NULL
            UNION ALL
            SELECT business_type, name, email, phone, website, address, specialty, rating
            FROM businesses WHERE email IS NOT NULL
            ORDER BY type, name
        ''')
        headers = ['Type', 'Name', 'Email', 'Phone', 'Website', 'Address', 'Specialty', 'Rating']
        filename = f'honolulu_all_leads_{datetime.now().strftime("%Y%m%d")}.csv'
    elif export_type == 'businesses':
        c.execute('SELECT business_type, name, email, phone, website, address, specialty, rating FROM businesses WHERE email IS NOT NULL')
        headers = ['Type', 'Name', 'Email', 'Phone', 'Website', 'Address', 'Specialty', 'Rating']
        filename = f'honolulu_businesses_{datetime.now().strftime("%Y%m%d")}.csv'
    else:
        c.execute('SELECT name, email, phone, website, address, floors, beachfront, star_rating FROM hotels WHERE email IS NOT NULL')
        headers = ['Hotel Name', 'Email', 'Phone', 'Website', 'Address', 'Floors', 'Beachfront', 'Star Rating']
        filename = f'honolulu_hotels_{datetime.now().strftime("%Y%m%d")}.csv'

    data = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(data)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    # Get API key from environment or request
    api_key = request.json.get('api_key') if request.json else None

    if not api_key:
        # SerpAPI key
        api_key = "69ba8b9b642039edc041e7259c22bcf76072009bc53150bcbb810b9cbd726a6d"

    try:
        result = scrape_hotels(api_key)
        return jsonify({
            "success": True,
            "count": result["saved"],
            "found": result["found"],
            "message": f"Successfully scraped {result['found']} hotels, saved {result['saved']} new ones"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5007)