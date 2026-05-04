import requests
import time
import json
import config
import threading
import asyncio
from datetime import datetime
import pytz
from messages import format_alert
from strategy import calculate_consensus

# --- CITY CONFIGURATION ---

class CityConfig:
    def __init__(self, city_display, tz_name, resolves_at_lat, resolves_at_lon, unit):
        self.city_display = city_display
        self.tz_name = tz_name
        self.resolves_at_lat = resolves_at_lat
        self.resolves_at_lon = resolves_at_lon
        self.unit = unit

# The core list of cities supported by Polymarket
SUPPORTED_CITIES = {
    "NYC": CityConfig("New York City", "America/New_York", 40.77, -73.97, "F"),
    "CHI": CityConfig("Chicago", "America/Chicago", 41.98, -87.90, "F"),
    "LA": CityConfig("Los Angeles", "America/Los_Angeles", 33.94, -118.40, "F"),
    "LON": CityConfig("London", "Europe/London", 51.47, -0.45, "C"),
    "TOK": CityConfig("Tokyo", "Asia/Tokyo", 35.54, 139.77, "C"),
    "PAR": CityConfig("Paris", "Europe/Paris", 49.00, 2.55, "C"),
    "DAL": CityConfig("Dallas", "America/Chicago", 32.89, -97.04, "F"),
    "HOU": CityConfig("Houston", "America/Chicago", 29.98, -95.34, "F"),
    "PHX": CityConfig("Phoenix", "America/Phoenix", 33.43, -112.01, "F"),
    "PHI": CityConfig("Philadelphia", "America/New_York", 39.87, -75.24, "F"),
}

# --- ENGINE LOGIC ---

def get_candidate_slugs(city_key, target_date):
    """Generates the specific URL formats Polymarket uses."""
    city_slug = city_key.lower()
    month = target_date.strftime("%B").lower()
    day = target_date.day
    year = target_date.year
    iso_date = target_date.strftime("%Y-%m-%d")

    return [
        f"highest-temperature-in-{city_slug}-on-{month}-{day}-{year}",
        f"highest-temperature-in-{city_slug}-{month}-{day}-{year}",
        f"highest-temperature-in-{city_slug}-on-{iso_date}",
    ]

async def find_market(city_key):
    """Attempts to find an active event by cycling through slug candidates[cite: 1]."""
    cfg = SUPPORTED_CITIES.get(city_key)
    if not cfg: return None

    # Get the date in the city's local timezone[cite: 1]
    tz = pytz.timezone(cfg.tz_name)
    local_today = datetime.now(tz)
    
    slugs = get_candidate_slugs(city_key, local_today)
    
    for slug in slugs:
        url = f"https://gamma-api.polymarket.com/events?slug={slug}"
        try:
            resp = requests.get(url).json()
            # If we get a valid list with an active event, return it[cite: 2]
            if isinstance(resp, list) and len(resp) > 0 and not resp[0].get('closed'):
                return {"event": resp[0], "cfg": cfg, "slug": slug}
        except:
            continue
    return None

async def analyze_city(city_key):
    """Analyzes weather vs market price for a specific city[cite: 2]."""
    data = await find_market(city_key)
    if not data:
        return f"❌ No active market found for {city_key} today."

    cfg = data['cfg']
    
    # Use exact airport coordinates from CityConfig for weather[cite: 1]
    w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={cfg.resolves_at_lat}&lon={cfg.resolves_at_lon}&appid={config.WEATHER_API_KEY}&units=metric"
    
    try:
        w_data = requests.get(w_url).json()
        models = {
            "hrrr": w_data['hourly'][0]['temp'],
            "ecmwf": w_data['daily'][0]['temp']['day'],
            "gfs": w_data['current']['temp']
        }
        
        temp, conf = calculate_consensus(models)
        return format_alert(cfg.city_display, "🎯 SURGICAL SCAN", conf, "N/A", temp, cfg.unit, f"ID: {data['slug'][:15]}...")
    except Exception as e:
        return f"⚠️ Weather error for {cfg.city_display}: {e}"

# --- TELEGRAM COMMANDS ---

def handle_commands():
    last_update_id = 0
    base_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
    print("📡 Command listener active.")
    
    while True:
        try:
            updates = requests.get(f"{base_url}/getUpdates?offset={last_update_id + 1}", timeout=10).json()
            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "").upper()
                chat_id = msg.get("chat", {}).get("id")
                
                if text.startswith("/CHECK"):
                    city_code = text.replace("/CHECK", "").strip()
                    if city_code in SUPPORTED_CITIES:
                        res = asyncio.run(analyze_city(city_code))
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": res, "parse_mode": "Markdown"})
                    else:
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": f"❌ Unknown city code. Try NYC, CHI, or LON."})
        except: pass
        time.sleep(1)

# --- BACKGROUND SCAN ---

def background_scan():
    """Loops through the 33 supported cities systematically."""
    while True:
        print(f"🔄 Starting surgical scan of {len(SUPPORTED_CITIES)} cities...")
        for city_key in SUPPORTED_CITIES.keys():
            res = asyncio.run(analyze_city(city_key))
            
            # Only send alert if a market was actually found
            if "🎯 SURGICAL" in res:
                print(f"✅ Market Found: {city_key}")
                requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", 
                             data={"chat_id": config.TELEGRAM_CHAT_ID, "text": res, "parse_mode": "Markdown"})
            
            time.sleep(5) # Prevent API rate limiting
            
        print("💤 Scan complete. Waiting 15 minutes...")
        time.sleep(900)

if __name__ == "__main__":
    threading.Thread(target=handle_commands, daemon=True).start()
    background_scan()
    
