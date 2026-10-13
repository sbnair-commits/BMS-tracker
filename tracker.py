import os
import sys
import requests

# --- CONFIGURATION ---
MOVIE_CODE = "ET00507359"       # MOVIE CODE
TARGET_THEATRE_CODE = "PMNK"    # PVR Mymoon, Kochi
TARGET_DATE = "20261011"        # YYYYMMDD (use a date that is still disabled to wait for it to open)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")



HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
    "Origin": "https://in.bookmyshow.com",
}

if os.getenv("BMS_COOKIE"):
    HEADERS["Cookie"] = os.getenv("BMS_COOKIE")


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram notification sent!")
            return True
        print(f"Telegram API error: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Failed to reach Telegram API: {e}")
    return False


def check_bookings():
    """Returns a list of show times if the movie is bookable at the venue, else None."""
    print(f"Querying BookMyShow for date {TARGET_DATE}...")
    response = requests.get(API_URL, headers=HEADERS, timeout=15)

    if response.status_code != 200:
        print(f"Endpoint returned status code: {response.status_code}")
        # Fail the workflow so a block shows up red in Actions instead of looking fine
        sys.exit(2)

    data = response.json()

    for day in data.get("ShowDetails", []):
        if day.get("Date") != TARGET_DATE:
            continue
        # "Venues" is a single object in this response, not a list
        if day.get("Venues", {}).get("VenueCode") != TARGET_THEATRE_CODE:
            continue
        for event in day.get("Event", []):
            for child in event.get("ChildEvents", []):
                if child.get("EventCode") == MOVIE_CODE and child.get("ShowTimes"):
                    return [s["ShowTime"] for s in child["ShowTimes"]]

    print("No showtimes for this movie at this venue yet.")
    return None


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID secrets.")
        sys.exit(1)
    if not API_URL:
        print("Error: missing BMS_API_URL secret (copy the URL from Postman).")
        sys.exit(1)

    shows = check_bookings()
    if shows:
        msg = (
            f"🚨 *ALERT!* Bookings are *OPEN* for *Avaraachan & Sons* "
            f"on {TARGET_DATE} at PVR Mymoon, Kochi!\n"
            f"Shows: {', '.join(shows)} 🎟️"
        )
        send_telegram_alert(msg)

