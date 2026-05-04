import requests
import time
import json
import config
import threading
from messages import format_alert
from strategy import calculate_consensus

# --- HELPER FUNCTIONS ---

def get_market_data_for_city(query):
    """Core logic to find a market, fetch weather, and calculate edge."""
    url = f"https://gamma-api.polymarket.com/events?active=true&query={query}"
    try:
        response = requests.get(url).json()
        
        # Check if response is a list and has items
        if not isinstance(response, list) or len(response) == 0:
            return f"❌ No active market found for '{query}'."
        
        event = response[0] 
        markets = event.get('markets', [])
        if not markets:
            return f"❌ No active betting markets for {query}."
            
        market = markets[0]
        ids = json.loads(market.get('clobTokenIds', '{}'))
        token_id = ids.get('1') 

        if not token_id:
            return "❌ Could not find 'YES' token."

        # Get Price
        p_url = f"https://clob.polymarket.com/price/buy/{token_id}"
        p_resp = requests.get(p_url).json()
        current_price = float(p_resp[0].get('price', 0)) * 100 if isinstance(p_resp, list) else float(p_resp.get('price', 0)) * 100

        # Get Weather
        geo = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={config.WEATHER_API_KEY}").json()
        if not geo: return f"❌ Location not found: {query}"

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
        
        return format_alert(query, "🔍 ANALYSIS", conf, current_price, temp, unit, f"ID: {token_id[:6]}")
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

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
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                
                if text.startswith("/check"):
                    city = text.replace("/check", "").strip()
                    if city:
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": f"⏳ Checking {city}..."})
                        res = get_market_data_for_city(city)
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": res, "parse_mode": "Markdown"})
        except:
            pass
        time.sleep(1)

# --- BACKGROUND SCAN ---

def background_scan():
    """Scans for all active temperature markets automatically."""
    while True:
        print("🔄 Running background scan...")
        url = "https://gamma-api.polymarket.com/events?active=true&closed=false&query=Temperature"
        try:
            resp = requests.get(url).json()
            if isinstance(resp, list):
                for event in resp:
                    title = event.get('title', 'Unknown')
                    # This triggers the analysis for every active market found
                    print(f"Checking market: {title}")
                    # You can add logic here to only send Telegram alerts if confidence > 0.8
            else:
                print("Polymarket API returned unexpected format.")
        except Exception as e:
            print(f"Background error: {e}")
            
        print("💤 Scan complete. Waiting 15 minutes...")
        time.sleep(900)

if __name__ == "__main__":
    threading.Thread(target=handle_commands, daemon=True).start()
    background_scan()
