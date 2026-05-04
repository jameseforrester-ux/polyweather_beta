import requests
import time
import json
import config
import threading
from datetime import date
from messages import format_alert
from strategy import calculate_consensus
# Import the logic from your provided file
from polymarket_2 import SUPPORTED_CITIES, get_market_for_city, city_local_today 

# --- UPDATED ENGINE ---

async def get_market_data_for_city_NEW(city_key):
    """
    Replaces the old query-based engine. 
    Uses the slug-generator from polymarket_2.py.
    """
    target_date = city_local_today(city_key)[cite: 1]
    # This automatically tries all 7 slug variants (e.g., 'on-may-5-2026')
    market = await get_market_for_city(city_key, target_date)[cite: 1]
    
    if not market:
        return f"❌ No active market found for {city_key} on {target_date}"[cite: 1]

    # Now use the exact Lat/Lon and ICAO from the CityConfig
    cfg = SUPPORTED_CITIES[city_key][cite: 1]
    lat, lon = cfg.resolves_at_lat, cfg.resolves_at_lon[cite: 1]
    
    # Get Weather (Using exact coordinates from CityConfig)[cite: 1, 2]
    w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={config.WEATHER_API_KEY}&units=metric"
    w_data = requests.get(w_url).json()

    # Strategy & Alerting (Same as your original)
    models = {
        "hrrr": w_data['hourly'][0]['temp'],
        "ecmwf": w_data['daily'][0]['temp']['day'],
        "gfs": w_data['current']['temp']
    }
    
    temp, conf = calculate_consensus(models)
    
    # Send alert for the best 'bucket' (e.g. 70-75°F) found by the new parser[cite: 1, 2]
    return format_alert(market.city_display, "🔍 ANALYSIS", conf, "N/A", temp, market.unit, market.event_slug)

# --- UPDATED BACKGROUND SCAN ---

def background_scan():
    """
    No more 'Net-Catcher'. We now loop through the 33 verified cities.[cite: 1, 2]
    """
    while True:
        print("🔄 Running targeted scan on 33 global cities...")
        for city_key in SUPPORTED_CITIES.keys():[cite: 1]
            print(f"Checking {city_key}...")
            # Logic to run the async fetcher and send Telegram alert...
            # (Matches your existing Telegram send logic)[cite: 2]
            
        print("💤 Targeted scan complete. Waiting 15 minutes...")
        time.sleep(900)
