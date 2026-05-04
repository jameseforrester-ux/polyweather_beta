import requests
import time
import json
import config
from messages import format_alert
from strategy import calculate_consensus

def get_active_weather_markets():
    """
    Scans Polymarket for all active daily temperature markets.
    Returns a list of dictionaries with city info and token IDs.
    """
    # This query looks for the 'Daily Temperature' series on Polymarket
    url = "https://gamma-api.polymarket.com/events?active=true&closed=false&query=Temperature"
    try:
        response = requests.get(url).json()
        active_list = []
        
        for event in response:
            for market in event.get('markets', []):
                # We want the 'YES' token for the price check
                ids = json.loads(market.get('clobTokenIds', '{}'))
                yes_token = ids.get('1')
                
                if yes_token:
                    active_list.append({
                        "name": market.get('groupItemTitle', event.get('title')),
                        "ticker": event.get('ticker'),
                        "token_id": yes_token,
                        "market_slug": market.get('slug')
                    })
        return active_list
    except Exception as e:
        print(f"Error scanning Polymarket: {e}")
        return []

def fetch_weather_for_market(market_name):
    """
    Since we don't have a list, we use OpenWeather's Geocoding 
    to find the Lat/Lon based on the Polymarket name.
    """
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={market_name}&limit=1&appid={config.WEATHER_API_KEY}"
    try:
        geo_data = requests.get(geo_url).json()
        if not geo_data: return None
        
        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
        
        # Now get the HRRR/ECMWF/GFS data
        w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={config.WEATHER_API_KEY}&units=metric"
        return requests.get(w_url).json()
    except:
        return None

def run_main_loop():
    print("🔭 Scanning Polymarket for live weather events...")
    
    while True:
        # 1. Get ONLY what is currently trading on Polymarket
        active_markets = get_active_weather_markets()
        
        for market in active_markets:
            # 2. Get the current price from CLOB
            p_url = f"https://clob.polymarket.com/price/buy/{market['token_id']}"
            price_data = requests.get(p_url).json()
            current_price = float(price_data.get('price', 0)) * 100
            
            # 3. Get weather for this specific market location
            w_data = fetch_weather_for_market(market['name'])
            
            if w_data:
                # Use your strategy.py weights (HRRR 45%, ECMWF 25%)
                models = {
                    "hrrr": w_data['hourly'][0]['temp'],
                    "ecmwf": w_data['daily'][0]['temp']['day'],
                    "gfs": w_data['current']['temp']
                }
                
                temp, conf = calculate_consensus(models)
                
                # Determine Unit (US markets are F, others C)
                unit = "C" if any(x in market['name'] for x in ["London", "Paris", "Sydney"]) else "F"
                
                msg = format_alert(
                    market['name'], 
                    "🟢 BUY" if conf > 0.8 else "⚪ NEUTRAL", 
                    conf, current_price, temp, unit, 
                    f"Market ID: {market['token_id'][:6]}"
                )
                
                # 4. Push to Telegram
                requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", 
                              data={"chat_id": config.TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                
            time.sleep(2) # Avoid rate limits
            
        print("💤 Scan complete. Sleeping for 15 minutes...")
        time.sleep(900)

if __name__ == "__main__":
    run_main_loop()
