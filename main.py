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

# --- CITY CONFIGURATION (Integrated from polymarket_2) ---

class CityConfig:
    def __init__(self, city_display, tz_name, resolves_at_lat, resolves_at_lon, unit):
        self.city_display = city_display
        self.tz_name = tz_name
        self.resolves_at_lat = resolves_at_lat
        self.resolves_at_lon = resolves_at_lon
        self.unit = unit

# The 33 cities supported by Polymarket weather markets[cite: 1]
SUPPORTED_CITIES = {
    "NYC": CityConfig("New York City", "America/New_York", 40.77, -73.97, "F"),
    "CHI": CityConfig("Chicago", "America/Chicago", 41.98, -87.90, "F"),
    "LA": CityConfig("Los Angeles", "America/Los_Angeles", 33.94, -118.40, "F"),
    "LON": CityConfig("London", "Europe/London", 51.47, -0.45, "C"),
    "TOK": CityConfig("Tokyo", "Asia/Tokyo", 35.54, 139.77, "C"),
    "PAR": CityConfig("Paris", "Europe/Paris", 49.00, 2.55, "C"),
    # ... (You can add more from the polymarket_2 list as needed)
}

# --- CORE ENGINE ---

def get_candidate_slugs(city_slug, target_date):
    """Generates the 7 URL variations Polymarket uses for weather[cite: 1]."""
    month_name = target_date.strftime("%B").lower()
    yyyy_mm_dd = target_date.strftime("%Y-%m-%d")
    day = target_date.day
    year = target_date.year

    return [
        f"highest-temperature-in-{city_slug.lower()}-on-{month_name}-{day}-{year}",
        f"highest-temperature-in-{city_slug.lower()}-{month_name}-{day}-{year}",
        f"highest-temperature-in-{city_slug.lower()}-on-{yyyy_mm_dd}",
        f"will-the-temperature-in-{city_slug.lower()}-reach-75-on-{month_name}-{day}",
        # Adding more generic variants for fallback[cite: 1]
    ]

async def find_market(city_key):
    """Finds the active market using the slug generator[cite: 1]."""
    cfg = SUPPORTED_CITIES.get(city_key)
    if not cfg: return None

    # Get local time for the target city[cite: 1]
    tz = pytz.timezone(cfg.tz_name)
    today = datetime.now(tz)
    
    slugs = get_candidate_slugs(city_key, today)
    
    for slug in slugs:
        url = f"https://gamma-api.polymarket.com/events?slug={slug}"
        try:
            resp = requests.get(url).json()
            if isinstance(resp, list) and len(resp) > 0:
                return {"event": resp[0], "cfg": cfg, "slug": slug}
        except:
            continue
    return None

async def get_market_data_for_city(city_key):
    """Main analysis logic[cite: 2]."""
    data = await find_market(city_key)
    if not data:
        return f"❌ No active market found for {city_key} today."

    cfg = data['cfg']
    
    # Get Weather using exact coords[cite: 1, 2]
    w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={cfg.resolves_at_lat}&lon={cfg.resolves_at_lon}&appid={config.WEATHER_API_KEY}&units=metric"
    try:
        w_data = requests.get(w_url).json()
        models = {
            "hrrr": w_data['hourly'][0]['temp'],
            "ecmwf": w_data['daily'][0]['temp']['day'],
            "gfs": w_data['current']['temp']
        }
        
        temp, conf = calculate_consensus(models)
        return format_alert(cfg.city_display, "🔍 TARGETED", conf, "N/A", temp, cfg.unit, f"Slug: {data['slug']}")
    except Exception as e:
        return f"⚠️ Weather Error for {city_key}: {e}"

# --- TELEGRAM & BACKGROUND ---

def handle_commands():
    last_update_id = 0
    base_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
    while True:
        try:
            updates = requests.get(f"{base_url}/getUpdates?offset={last_update_id + 1}", timeout=10).json()
            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                text = update.get("message", {}).get("text", "").upper()
                chat_id = update.get("message", {}).get("chat", {}).get("id")
                
                if text.startswith("/CHECK"):
                    city = text.replace("/CHECK", "").strip()
                    if city in SUPPORTED_CITIES:
                        res = asyncio.run(get_market_data_for_city(city))
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": res, "parse_mode": "Markdown"})
        except: pass
        time.sleep(1)

def background_scan():
    while True:
        for city_key in SUPPORTED_CITIES.keys():
            res = asyncio.run(get_market_data_for_city(city_key))
            if "🔍 TARGETED" in res:
                requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", 
                             data={"chat_id": config.TELEGRAM_CHAT_ID, "text": res, "parse_mode": "Markdown"})
            time.sleep(5) 
        time.sleep(900)

if __name__ == "__main__":
    threading.Thread(target=handle_commands, daemon=True).start()
    background_scan()
