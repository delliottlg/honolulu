import requests
from serpapi import GoogleSearch
import sqlite3
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

class HonoluluHotelScraper:
    def __init__(self, serpapi_key):
        self.serpapi_key = serpapi_key
        self.db_path = 'honolulu_hotels.db'

    def search_hotels(self):
        """Search for hotels in Honolulu using SerpAPI"""
        params = {
            "api_key": self.serpapi_key,
            "engine": "google_maps",
            "q": "hotels in Honolulu Hawaii",
            "ll": "@21.3099,157.8581,11z",  # Centered on Honolulu
            "type": "search",
            "limit": 50  # Get up to 50 results
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        hotels = []
        if "local_results" in results:
            for place in results["local_results"]:
                hotel_data = self.extract_hotel_info(place)
                if hotel_data:
                    hotels.append(hotel_data)

        # Also search for specific high-value areas
        areas = ["Waikiki hotels", "Ko Olina hotels Hawaii", "Kahala hotels Honolulu"]
        for area in areas:
            params["q"] = area
            search = GoogleSearch(params)
            area_results = search.get_dict()
            if "local_results" in area_results:
                for place in area_results["local_results"]:
                    hotel_data = self.extract_hotel_info(place)
                    if hotel_data and hotel_data not in hotels:
                        hotels.append(hotel_data)

        return hotels

    def extract_hotel_info(self, place):
        """Extract hotel information from SerpAPI result"""
        try:
            # Skip if not actually a hotel/resort
            if place.get("type") and not any(keyword in place.get("type", "").lower()
                                            for keyword in ["hotel", "resort", "inn", "lodge"]):
                return None

            hotel = {
                "name": place.get("title", ""),
                "address": place.get("address", ""),
                "phone": place.get("phone", ""),
                "website": place.get("website", ""),
                "star_rating": place.get("rating"),
                "property_type": place.get("type", "hotel"),
                "beachfront": self.is_beachfront(place),
                "floors": self.estimate_floors(place),
                "email": None  # Will try to find this
            }

            # Try to get email from website
            if hotel["website"]:
                hotel["email"] = self.find_email(hotel["website"], hotel["name"])

            return hotel
        except Exception as e:
            print(f"Error extracting hotel info: {e}")
            return None

    def is_beachfront(self, place):
        """Determine if hotel is beachfront based on name/address"""
        beachfront_keywords = ["beach", "beachfront", "oceanfront", "ocean view",
                              "waikiki", "seaside", "shore", "kai"]
        text = f"{place.get('title', '')} {place.get('address', '')}".lower()
        return any(keyword in text for keyword in beachfront_keywords)

    def estimate_floors(self, place):
        """Estimate floors based on hotel name/type"""
        # High-rise indicators
        if any(word in place.get("title", "").lower()
               for word in ["tower", "high-rise", "hilton", "sheraton", "hyatt"]):
            return 20  # Estimate for major chains
        return None

    def find_email(self, website, hotel_name):
        """Try to find email from hotel website"""
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]

        # Common hotel email patterns
        domain = urlparse(website).netloc.replace("www.", "")
        common_emails = [
            f"info@{domain}",
            f"reservations@{domain}",
            f"sales@{domain}",
            f"gm@{domain}",
            f"contact@{domain}"
        ]

        try:
            # First try to scrape the website
            response = requests.get(website, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for emails in text
                text = soup.get_text()
                for pattern in email_patterns:
                    matches = re.findall(pattern, text)
                    for email in matches:
                        if not email.endswith('.png') and not email.endswith('.jpg'):
                            return email

                # Look for mailto links
                for link in soup.find_all('a', href=True):
                    if 'mailto:' in link['href']:
                        email = link['href'].replace('mailto:', '').split('?')[0]
                        return email
        except:
            pass

        # Return most likely common email
        return common_emails[0] if domain else None

    def save_to_database(self, hotels):
        """Save hotels to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        saved_count = 0
        for hotel in hotels:
            try:
                # Check if hotel already exists
                c.execute("SELECT id FROM hotels WHERE name = ?", (hotel["name"],))
                if c.fetchone() is None:
                    c.execute("""INSERT INTO hotels
                              (name, address, phone, email, website, property_type,
                               floors, beachfront, star_rating, city, state)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Honolulu', 'HI')""",
                              (hotel["name"], hotel["address"], hotel["phone"],
                               hotel["email"], hotel["website"], hotel["property_type"],
                               hotel["floors"], hotel["beachfront"], hotel["star_rating"]))
                    saved_count += 1
            except Exception as e:
                print(f"Error saving hotel {hotel['name']}: {e}")

        conn.commit()
        conn.close()
        return saved_count

    def run(self):
        """Main scraping function"""
        print("Starting Honolulu hotel scraping...")
        hotels = self.search_hotels()
        print(f"Found {len(hotels)} hotels")

        saved = self.save_to_database(hotels)
        print(f"Saved {saved} new hotels to database")

        return {"found": len(hotels), "saved": saved}

# Function to be called from Flask
def scrape_hotels(api_key):
    scraper = HonoluluHotelScraper(api_key)
    return scraper.run()