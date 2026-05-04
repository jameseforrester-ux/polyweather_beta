import requests
import time
import json
import config
import threading
from messages import format_alert
from strategy import calculate_consensus

# --- HELPER FUNCTIONS ---

def get_market_data_for_city(query):
    """The core engine to find a market, get weather, and calculate edge."""
    url = f"https://gamma-api.polymarket.com/events?active=true&query={query}"
    try:
        response = requests.get(url).json()
        
        # Check if the response is a valid list with data
        if not isinstance(response, list) or len(response) == 0:
            return f"❌ No active market found for '{query}'."
        
        event = response[0] 
        markets = event.get('markets', [])
        if not markets:
            return f"❌ Event found for {query}, but no active betting markets."
            
        market = markets[0]
        
        # Parse Token IDs for the 'YES' side
        clob_ids_raw = market.get('clobTokenIds', '{}')
        ids = json.loads(clob_ids_raw)
        token_id = ids.get('1') 

        if not token_id:
            return "❌ Could not find a 'YES' token for this market."

        # Get Price from Polymarket CLOB
        p_url = f"https://clob.polymarket.com/price/buy/{token_id}"
        price_resp = requests.get(p_url).json()
        
        # Handle cases where price API returns a list vs a dict
        if isinstance(price_resp, list) and len(price_resp) > 0:
            current_price = float(price_resp[0].get('price', 0)) * 100
        else:
            current_price = float(price_resp.get('price', 0)) * 100

        # Get Weather Coordinates
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={config.WEATHER_API_KEY}"
        geo = requests.get(geo_url).json()
        
        if not geo:
            return f"❌ OpenWeather couldn't find coordinates for {query}."

        # Get Weather Model Data
        lat, lon = geo[0]['lat'], geo[0]['lon']
        w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={config.WEATHER_API_KEY}&units=metric"
        w_data = requests.get(w_url).json()

        models = {
            "hrrr": w_data['hourly'][0]['temp'],
            "ecmwf": w_data['daily'][0]['temp']['day'],
            "gfs": w_data['current']['temp']
        }
        
        temp, conf = calculate_consensus(models)
        unit = "C" if any(x in query.lower() for x in ["london", "paris", "tokyo", "sydney"]) else "F"
        
        return format_alert(query, "🔍 MANUAL LOOKUP", conf, current_price, temp, unit, f"ID: {token_id[:6]}")
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- TELEGRAM INTERACTION ---

def handle_commands():
    """Listens for /check commands in Telegram."""
    last_update_id = 0
    base_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
    
    print("📡 Command listener active. Type /check [City] in Telegram.")
    
    while True:
        try:
            updates = requests.get(f"{base_url}/getUpdates?offset={last_update_id + 1}", timeout=10).json()
            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message", {})
                msg_text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                
                if msg_text.startswith("/check"):
                    city_query = msg_text.replace("/check", "").strip()
                    if not city_query:
                        response_text = "Please provide a city name. Example: `/check Chicago`"
                    else:
                        # Send "Typing..." notification
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": f"⏳ Analyzing {city_query}..."})
                        response_text = get_market_data_for_city(city_query)
                    
                    requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": response_text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Update error: {e}")
        time.sleep(1)

# --- BACKGROUND LOOP ---

def background_scan():
    """Automated 15-minute background monitoring."""
    while True:
        print("🔄 Running scheduled background scan...")
        # (This is where your automated scan logic resides)
        time.sleep(900)

if __name__ == "__main__":
    # Start the command listener in a background thread
    t = threading.Thread(target=handle_commands)
    t.daemon = True
    t.start()
    
    # Run the main scan loop in the foreground
    background_scan()
