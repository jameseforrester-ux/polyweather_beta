import requests
import time
import json
import config
from messages import format_alert
from strategy import calculate_consensus

# 1. The Full 36 City List with Coordinates for Airport Weather Stations
ALL_CITIES = [
    # --- East ---
    {"name": "New York (JFK)", "unit": "F", "lat": 40.6413, "lon": -73.7781, "ticker": "NYC-TEMP"},
    {"name": "Newark (EWR)", "unit": "F", "lat": 40.6895, "lon": -74.1745, "ticker": "EWR-TEMP"},
    {"name": "Boston (BOS)", "unit": "F", "lat": 42.3656, "lon": -71.0096, "ticker": "BOS-TEMP"},
    {"name": "Philadelphia (PHL)", "unit": "F", "lat": 39.8729, "lon": -75.2437, "ticker": "PHL-TEMP"},
    {"name": "Washington (IAD)", "unit": "F", "lat": 38.9445, "lon": -77.4558, "ticker": "IAD-TEMP"},
    {"name": "Atlanta (ATL)", "unit": "F", "lat": 33.6407, "lon": -84.4277, "ticker": "ATL-TEMP"},
    {"name": "Miami (MIA)", "unit": "F", "lat": 25.7959, "lon": -80.2870, "ticker": "MIA-TEMP"},
    {"name": "Orlando (MCO)", "unit": "F", "lat": 28.4312, "lon": -81.3081, "ticker": "MCO-TEMP"},
    {"name": "Charlotte (CLT)", "unit": "F", "lat": 35.2144, "lon": -80.9473, "ticker": "CLT-TEMP"},
    
    # --- Midwest ---
    {"name": "Chicago (ORD)", "unit": "F", "lat": 41.9742, "lon": -87.9073, "ticker": "CHI-TEMP"},
    {"name": "Minneapolis (MSP)", "unit": "F", "lat": 44.8848, "lon": -93.2223, "ticker": "MSP-TEMP"},
    {"name": "Detroit (DTW)", "unit": "F", "lat": 42.2125, "lon": -83.3533, "ticker": "DTW-TEMP"},
    {"name": "St. Louis (STL)", "unit": "F", "lat": 38.7477, "lon": -90.3597, "ticker": "STL-TEMP"},
    {"name": "Columbus (CMH)", "unit": "F", "lat": 39.9999, "lon": -82.8919, "ticker": "CMH-TEMP"},
    {"name": "Cincinnati (CVG)", "unit": "F", "lat": 39.0461, "lon": -84.6625, "ticker": "CVG-TEMP"},
    
    # --- South/Texas ---
    {"name": "Dallas (DFW)", "unit": "F", "lat": 32.8998, "lon": -97.0403, "ticker": "DFW-TEMP"},
    {"name": "Houston (IAH)", "unit": "F", "lat": 29.9902, "lon": -95.3368, "ticker": "IAH-TEMP"},
    {"name": "Austin (AUS)", "unit": "F", "lat": 30.1975, "lon": -97.6664, "ticker": "AUS-TEMP"},
    {"name": "Nashville (BNA)", "unit": "F", "lat": 36.1263, "lon": -86.6774, "ticker": "BNA-TEMP"},
    {"name": "New Orleans (MSY)", "unit": "F", "lat": 29.9911, "lon": -90.2592, "ticker": "MSY-TEMP"},
    
    # --- West ---
    {"name": "Denver (DEN)", "unit": "F", "lat": 39.8561, "lon": -104.6737, "ticker": "DEN-TEMP"},
    {"name": "Phoenix (PHX)", "unit": "F", "lat": 33.4342, "lon": -112.0080, "ticker": "PHX-TEMP"},
    {"name": "Las Vegas (LAS)", "unit": "F", "lat": 36.0840, "lon": -115.1537, "ticker": "LAS-TEMP"},
    {"name": "Salt Lake (SLC)", "unit": "F", "lat": 40.7899, "lon": -111.9791, "ticker": "SLC-TEMP"},
    {"name": "Los Angeles (LAX)", "unit": "F", "lat": 33.9416, "lon": -118.4085, "ticker": "LAX-TEMP"},
    {"name": "San Francisco (SFO)", "unit": "F", "lat": 37.6213, "lon": -122.3790, "ticker": "SFO-TEMP"},
    {"name": "Seattle (SEA)", "unit": "F", "lat": 47.4502, "lon": -122.3088, "ticker": "SEA-TEMP"},
    {"name": "Portland (PDX)", "unit": "F", "lat": 45.5891, "lon": -122.5935, "ticker": "PDX-TEMP"},
    
    # --- International ---
    {"name": "London (LHR)", "unit": "C", "lat": 51.4700, "lon": -0.4543, "ticker": "LON-TEMP"},
    {"name": "Paris (CDG)", "unit": "C", "lat": 49.0097, "lon": 2.5479, "ticker": "PAR-TEMP"},
    {"name": "Frankfurt (FRA)", "unit": "C", "lat": 50.0379, "lon": 8.5622, "ticker": "FRA-TEMP"},
    {"name": "Tokyo (HND)", "unit": "C", "lat": 35.5494, "lon": 139.7798, "ticker": "HND-TEMP"},
    {"name": "Sydney (SYD)", "unit": "C", "lat": -33.9399, "lon": 151.1753, "ticker": "SYD-TEMP"},
    {"name": "Toronto (YYZ)", "unit": "C", "lat": 43.6777, "lon": -79.6248, "ticker": "YYZ-TEMP"}
]

def get_live_id(ticker):
    """Automatically finds the correct active YES token on Polymarket."""
    try:
        url = f"https://gamma-api.polymarket.com/events?active=true&query={ticker}"
        data = requests.get(url).json()
        market = data[0]['markets'][0]
        ids = json.loads(market['clobTokenIds'])
        return ids['1'] # Returns the 'YES' token ID
    except:
        return None

def fetch_market_data(city):
    """Gathers real-time data from OpenWeather and Polymarket CLOB."""
    token_id = get_live_id(city['ticker'])
    if not token_id:
        return None

    try:
        # Weather Models (HRRR/ECMWF Weights applied in strategy.py)
        w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={city['lat']}&lon={city['lon']}&appid={config.WEATHER_API_KEY}&units=metric"
        w_data = requests.get(w_url).json()

        # CLOB Market Price
        p_url = f"https://clob.polymarket.com/price/buy/{token_id}"
        p_price = float(requests.get(p_url).json().get('price', 0)) * 100

        return {
            "price": p_price,
            "models": {
                "hrrr": w_data['hourly'][0]['temp'], 
                "ecmwf": w_data['daily'][0]['temp']['day'],
                "gfs": w_data['current']['temp']
            }
        }
    except Exception as e:
        print(f"Error fetching {city['name']}: {e}")
        return None

def run_main_loop():
    print("🚀 Monitoring 36 Cities via Automated Discovery...")
    while True:
        for city in ALL_CITIES:
            data = fetch_market_data(city)
            if data:
                # Use strategy.py for HRRR (45%) and ECMWF (25%) weights
                temp, conf = calculate_consensus(data['models'])
                
                # Signal is Green if confidence exceeds 80%
                signal = "🟢 BUY" if conf > 0.8 else "⚪ NEUTRAL"
                
                msg = format_alert(
                    city['name'], signal, conf, data['price'], 
                    temp, city['unit'], "Live automated consensus check."
                )
                
                # Push to Telegram
                requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", 
                              data={"chat_id": config.TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                print(f"✅ Alert sent: {city['name']}")
            
            time.sleep(3) # Small delay to stay under API limits
        
        print("💤 Cycle complete. Waiting 15 minutes...")
        time.sleep(900)

if __name__ == "__main__":
    run_main_loop()
