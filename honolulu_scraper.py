import requests
from serpapi import GoogleSearch
import sqlite3
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

class HonoluluGlassIndustryScraper:
    """Comprehensive Honolulu glass industry lead scraper"""

    def __init__(self, serpapi_key):
        self.serpapi_key = serpapi_key
        self.db_path = 'honolulu_hotels.db'  # Keep same database!
        self.init_database()

    def init_database(self):
        """Create comprehensive glass industry database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Keep hotels table with existing data!
        # Create comprehensive business table alongside hotels
        c.execute('''CREATE TABLE IF NOT EXISTS businesses
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      business_type TEXT NOT NULL,
                      address TEXT,
                      city TEXT DEFAULT 'Honolulu',
                      state TEXT DEFAULT 'HI',
                      zip_code TEXT,
                      phone TEXT,
                      email TEXT,
                      website TEXT,
                      specialty TEXT,
                      employees_estimate TEXT,
                      rating REAL,
                      reviews_count INTEGER,
                      years_in_business INTEGER,
                      license_number TEXT,
                      insurance_verified BOOLEAN DEFAULT 0,
                      hurricane_experience BOOLEAN DEFAULT 0,
                      commercial_projects BOOLEAN DEFAULT 0,
                      residential_projects BOOLEAN DEFAULT 0,
                      decision_maker TEXT,
                      notes TEXT,
                      date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def search_all_categories(self):
        """Search for all glass-related businesses in Honolulu"""
        all_businesses = []

        # Comprehensive search categories for Honolulu glass industry
        search_queries = [
            # HOTELS (keeping original)
            {"query": "hotels in Honolulu Hawaii", "type": "hotel", "specialty": "hospitality"},
            {"query": "Waikiki hotels", "type": "hotel", "specialty": "beachfront hospitality"},

            # GLASS CONTRACTORS & INSTALLERS
            {"query": "glass contractors Honolulu", "type": "glass_contractor", "specialty": "installation"},
            {"query": "window installation Honolulu", "type": "glass_contractor", "specialty": "window installation"},
            {"query": "storefront glass Honolulu", "type": "glass_contractor", "specialty": "commercial glass"},
            {"query": "glass repair Honolulu", "type": "glass_contractor", "specialty": "repair services"},
            {"query": "hurricane glass installers Hawaii", "type": "glass_contractor", "specialty": "hurricane glass"},

            # GLASS SUPPLIERS & DISTRIBUTORS
            {"query": "glass suppliers Honolulu", "type": "glass_supplier", "specialty": "wholesale glass"},
            {"query": "glass distributors Hawaii", "type": "glass_distributor", "specialty": "distribution"},
            {"query": "architectural glass Honolulu", "type": "glass_supplier", "specialty": "architectural"},
            {"query": "laminated glass suppliers Hawaii", "type": "glass_supplier", "specialty": "safety glass"},

            # CONSTRUCTION & PAINTING
            {"query": "general contractors Honolulu", "type": "general_contractor", "specialty": "construction"},
            {"query": "commercial contractors Hawaii", "type": "general_contractor", "specialty": "commercial"},
            {"query": "painters Honolulu commercial", "type": "painter", "specialty": "commercial painting"},
            {"query": "construction companies Honolulu", "type": "construction", "specialty": "new construction"},

            # GLASS ART & SPECIALTY
            {"query": "glass art Honolulu", "type": "glass_art", "specialty": "artistic glass"},
            {"query": "stained glass Honolulu", "type": "glass_art", "specialty": "stained glass"},
            {"query": "custom glass fabrication Hawaii", "type": "glass_fabricator", "specialty": "custom work"},
            {"query": "glass etching Honolulu", "type": "glass_art", "specialty": "etching"},

            # PROPERTY MANAGEMENT & DEVELOPERS
            {"query": "property management companies Honolulu", "type": "property_management", "specialty": "building management"},
            {"query": "real estate developers Hawaii", "type": "developer", "specialty": "development"},
            {"query": "commercial property managers Honolulu", "type": "property_management", "specialty": "commercial"},

            # ARCHITECTS & DESIGNERS
            {"query": "architects Honolulu commercial", "type": "architect", "specialty": "commercial design"},
            {"query": "architectural firms Hawaii", "type": "architect", "specialty": "architecture"},

            # HIGH-VALUE TARGETS
            {"query": "casinos Hawaii", "type": "casino", "specialty": "gaming"},
            {"query": "hospitals Honolulu", "type": "hospital", "specialty": "healthcare"},
            {"query": "schools Honolulu private", "type": "school", "specialty": "education"},
            {"query": "shopping centers Honolulu", "type": "retail", "specialty": "retail complex"},
            {"query": "office buildings Honolulu", "type": "office", "specialty": "commercial office"}
        ]

        for search_item in search_queries:
            print(f"Searching for: {search_item['query']}")
            businesses = self.search_google_maps(
                search_item['query'],
                search_item['type'],
                search_item['specialty']
            )
            all_businesses.extend(businesses)
            time.sleep(1)  # Be nice to the API

        return all_businesses

    def search_google_maps(self, query, business_type, specialty):
        """Search Google Maps for specific business type"""
        params = {
            "api_key": self.serpapi_key,
            "engine": "google_maps",
            "q": query,
            "ll": "@21.3099,-157.8581,12z",  # Honolulu center, wider radius
            "type": "search",
            "limit": 20  # Get up to 20 per search
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            businesses = []
            if "local_results" in results:
                for place in results["local_results"]:
                    business_data = self.extract_business_info(place, business_type, specialty)
                    if business_data:
                        businesses.append(business_data)

            return businesses
        except Exception as e:
            print(f"Error searching {query}: {e}")
            return []

    def extract_business_info(self, place, business_type, specialty):
        """Extract business information from SerpAPI result"""
        try:
            business = {
                "name": place.get("title", ""),
                "business_type": business_type,
                "specialty": specialty,
                "address": place.get("address", ""),
                "phone": place.get("phone", ""),
                "website": place.get("website", ""),
                "rating": place.get("rating"),
                "reviews_count": place.get("reviews", 0),
                "email": None
            }

            # Estimate company size from reviews
            if business["reviews_count"] > 100:
                business["employees_estimate"] = "50+"
            elif business["reviews_count"] > 50:
                business["employees_estimate"] = "20-50"
            else:
                business["employees_estimate"] = "1-20"

            # Check for hurricane/commercial experience in description
            description = place.get("description", "").lower()
            business["hurricane_experience"] = any(word in description for word in ["hurricane", "impact", "storm"])
            business["commercial_projects"] = any(word in description for word in ["commercial", "business", "office"])
            business["residential_projects"] = any(word in description for word in ["residential", "home", "house"])

            # Try to get email
            if business["website"]:
                business["email"] = self.find_email(business["website"], business["name"])

            return business
        except Exception as e:
            print(f"Error extracting business info: {e}")
            return None

    def find_email(self, website, business_name):
        """Enhanced email finder for various business types"""
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]

        # Generate likely email patterns based on domain
        domain = urlparse(website).netloc.replace("www.", "")

        # Different email patterns for different business types
        common_emails = [
            f"info@{domain}",
            f"contact@{domain}",
            f"sales@{domain}",
            f"admin@{domain}",
            f"office@{domain}",
            f"hello@{domain}",
            f"inquiries@{domain}",
            f"service@{domain}",
            f"support@{domain}",
            f"estimating@{domain}",  # For contractors
            f"quotes@{domain}",       # For suppliers
            f"orders@{domain}",       # For distributors
        ]

        try:
            response = requests.get(website, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

                # Look for emails in text
                for pattern in email_patterns:
                    matches = re.findall(pattern, text)
                    for email in matches:
                        if not email.endswith(('.png', '.jpg', '.gif')):
                            return email

                # Look for mailto links
                for link in soup.find_all('a', href=True):
                    if 'mailto:' in link['href']:
                        email = link['href'].replace('mailto:', '').split('?')[0]
                        return email

                # Check contact page
                for link in soup.find_all('a', href=True):
                    if 'contact' in link['href'].lower():
                        contact_url = requests.compat.urljoin(website, link['href'])
                        contact_response = requests.get(contact_url, timeout=3)
                        if contact_response.status_code == 200:
                            contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                            contact_text = contact_soup.get_text()
                            for pattern in email_patterns:
                                matches = re.findall(pattern, contact_text)
                                for email in matches:
                                    if not email.endswith(('.png', '.jpg', '.gif')):
                                        return email
        except:
            pass

        # Return most likely common email
        return common_emails[0] if domain else None

    def save_to_database(self, businesses):
        """Save businesses to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        saved_count = 0
        for business in businesses:
            try:
                # Check if business already exists
                c.execute("SELECT id FROM businesses WHERE name = ? AND business_type = ?",
                         (business["name"], business["business_type"]))
                if c.fetchone() is None:
                    c.execute("""INSERT INTO businesses
                              (name, business_type, specialty, address, phone, email, website,
                               rating, reviews_count, employees_estimate, hurricane_experience,
                               commercial_projects, residential_projects, city, state)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Honolulu', 'HI')""",
                              (business["name"], business["business_type"], business["specialty"],
                               business["address"], business["phone"], business["email"],
                               business["website"], business["rating"], business["reviews_count"],
                               business["employees_estimate"], business["hurricane_experience"],
                               business["commercial_projects"], business["residential_projects"]))
                    saved_count += 1
            except Exception as e:
                print(f"Error saving business {business['name']}: {e}")

        conn.commit()
        conn.close()
        return saved_count

    def run(self):
        """Main scraping function"""
        print("Starting comprehensive Honolulu glass industry scraping...")
        businesses = self.search_all_categories()
        print(f"Found {len(businesses)} total businesses")

        # Remove duplicates
        unique_businesses = []
        seen = set()
        for b in businesses:
            key = (b["name"], b["business_type"])
            if key not in seen:
                seen.add(key)
                unique_businesses.append(b)

        saved = self.save_to_database(unique_businesses)
        print(f"Saved {saved} new businesses to database")

        # Print summary
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT business_type, COUNT(*), COUNT(email)
                    FROM businesses
                    GROUP BY business_type""")

        print("\n=== Summary by Business Type ===")
        for row in c.fetchall():
            print(f"{row[0]}: {row[1]} total, {row[2]} with emails")

        conn.close()

        return {"found": len(unique_businesses), "saved": saved}

# Function to be called from Flask
def scrape_honolulu_glass_industry(api_key):
    scraper = HonoluluGlassIndustryScraper(api_key)
    return scraper.run()