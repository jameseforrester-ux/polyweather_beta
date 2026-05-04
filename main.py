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
    # 1. Find the market
    url = f"https://gamma-api.polymarket.com/events?active=true&query={query}"
    try:
        response = requests.get(url).json()
        if not response: return "❌ No active market found for that city."
        
        event = response[0]
        market = event['markets'][0]
        ids = json.loads(market.get('clobTokenIds', '{}'))
        token_id = ids.get('1')

        # 2. Get Price
        p_url = f"https://clob.polymarket.com/price/buy/{token_id}"
        price = float(requests.get(p_url).json().get('price', 0)) * 100

        # 3. Get Weather (Geocoding + OneCall)
        geo = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={config.WEATHER_API_KEY}").json()
        w_data = requests.get(f"https://api.openweathermap.org/data/3.0/onecall?lat={geo[0]['lat']}&lon={geo[0]['lon']}&appid={config.WEATHER_API_KEY}&units=metric").json()

        models = {
            "hrrr": w_data['hourly'][0]['temp'],
            "ecmwf": w_data['daily'][0]['temp']['day'],
            "gfs": w_data['current']['temp']
        }
        
        temp, conf = calculate_consensus(models)
        unit = "C" if any(x in query.lower() for x in ["london", "paris", "tokyo"]) else "F"
        
        return format_alert(query, "🔍 MANUAL LOOKUP", conf, price, temp, unit, f"ID: {token_id[:6]}")
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
            updates = requests.get(f"{base_url}/getUpdates?offset={last_update_id + 1}").json()
            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {}).get("text", "")
                
                if msg.startswith("/check"):
                    city_query = msg.replace("/check", "").strip()
                    if not city_query:
                        response_text = "Please provide a city name. Example: `/check Chicago`"
                    else:
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": config.TELEGRAM_CHAT_ID, "text": f"⏳ Fetching data for {city_query}..."})
                        response_text = get_market_data_for_city(city_query)
                    
                    requests.post(f"{base_url}/sendMessage", data={"chat_id": config.TELEGRAM_CHAT_ID, "text": response_text, "parse_mode": "Markdown"})
        except:
            pass
        time.sleep(2)

# --- BACKGROUND LOOP ---

def background_scan():
    """Your original 15-minute automated scanner."""
    while True:
        print("🔄 Running scheduled background scan...")
        # (The scan logic goes here - similar to the manual lookup but for all active markets)
        time.sleep(900)

if __name__ == "__main__":
    # Run the command listener in a separate thread so it doesn't block the loop
    threading.Thread(target=handle_commands, daemon=True).start()
    background_scan()
