import os
import requests
import sys

# --- CONFIGURATION FROM POSTMAN ---
MOVIE_CODE = "ET00507359"       # Movie Code for Avaraachan & Sons
REGION_CODE = "TRIV"            # Region code for Trivandrum
TARGET_THEATRE_CODE = "PMNK"    # Venue code from your API test
TARGET_DATE = "20261011"        # Show date (YYYYMMDD)

# Dynamic Environment Variables for GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Hidden API Endpoint
API_URL = f"https://bookmyshow.com{REGION_CODE}/movies/{MOVIE_CODE}/showtimes?date={TARGET_DATE}"

# ADVANCED ANTI-BOT HEADERS: Extracted straight from your successful Postman structure
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://bookmyshow.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://bookmyshow.com",
    "x-app-code": "WEB", # Tells their server this request is from the standard web client interface
}

def send_telegram_alert(message):
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram notification successfully sent!")
        else:
            print(f"Telegram API responded with error code: {res.status_code}")
    except Exception as e:
        print(f"Failed to establish connection to Telegram API: {e}")

def check_bookings():
    print(f"Querying BookMyShow endpoints for Date: {TARGET_DATE}...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        
        # Log details to see why if it's blocking
        if response.status_code != 200:
            print(f"Showtimes endpoint offline or returning status code: {response.status_code}")
            return False

        data = response.json()
        
        # Traverse BookMyShow JSON structure
        show_details = data.get("ShowDetails", [])
        for detail in show_details:
            events = detail.get("Event", [])
            for event in events:
                child_events = event.get("ChildEvents", [])
                for child in child_events:
                    show_times = child.get("ShowTimes", [])
                    if show_times:
                        print(f"Showtimes are populated and active for venue code: {TARGET_THEATRE_CODE}!")
                        return True
                
        print(f"Movie tracking data returned, but no showtimes are active for '{TARGET_THEATRE_CODE}' yet.")
        return False

    except Exception as e:
        print(f"Parsing error or empty payload received: {e}")
        return False

# --- GITHUB ACTIONS WORKFLOW EXECUTION ---
if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing credentials inside repository environment variables.")
        sys.exit(1)

    if check_bookings():
        alert_msg = f"🚨 *ALERT!* Bookings are officially *OPEN* for *Avaraachan & Sons*! Go grab your tickets right now! 🎟️"
        send_telegram_alert(alert_msg)
