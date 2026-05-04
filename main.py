import requests
import time
import json
import config
import threading
from messages import format_alert
from strategy import calculate_consensus

# --- HELPER FUNCTIONS ---

def get_market_data_for_city(query):
    """Core engine to find a market, fetch weather, and calculate edge."""
    # We query Gamma for the specific ticker or slug provided
    url = f"https://gamma-api.polymarket.com/events?active=true&query={query}"
    try:
        response = requests.get(url).json()
        if not isinstance(response, list) or len(response) == 0:
            return f"❌ No market found for '{query}'."
        
        event = response[0] 
        markets = event.get('markets', [])
        if not markets:
            return f"❌ No betting markets for {query}."
            
        market = markets[0]
        ids = json.loads(market.get('clobTokenIds', '{}'))
        token_id = ids.get('1') # YES Token

        if not token_id:
            return "❌ Missing 'YES' token."

        # Get Price from CLOB
        p_url = f"https://clob.polymarket.com/price/buy/{token_id}"
        p_resp = requests.get(p_url).json()
        
        if isinstance(p_resp, list) and len(p_resp) > 0:
            current_price = float(p_resp[0].get('price', 0)) * 100
        else:
            current_price = float(p_resp.get('price', 0)) * 100

        # Extract city from query or title for weather lookup
        # If query is 'NYC-TEMP', we look for 'New York'
        city_name = query.split('-')[0] if '-' in query else query

        # Get Weather
        geo = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={config.WEATHER_API_KEY}").json()
        if not geo: return f"❌ Location error: {city_name}"

        lat, lon = geo[0]['lat'], geo[0]['lon']
        w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={config.WEATHER_API_KEY}&units=metric"
        w_data = requests.get(w_url).json()

        models = {
            "hrrr": w_data['hourly'][0]['temp'],
            "ecmwf": w_data['daily'][0]['temp']['day'],
            "gfs": w_data['current']['temp']
        }
        
        temp, conf = calculate_consensus(models)
        unit = "C" if any(x in city_name.lower() for x in ["london", "paris", "tokyo", "sydney"]) else "F"
        
        return format_alert(city_name, "🔍 ANALYSIS", conf, current_price, temp, unit, f"ID: {token_id[:6]}")
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
    """Scans for active temperature markets using slug patterns."""
    while True:
        print("🔄 Running background scan...")
        # Use a broader query to ensure we catch markets, then filter manually
        url = "https://gamma-api.polymarket.com/events?active=true&query=Temperature"
        try:
            resp = requests.get(url).json()
            if isinstance(resp, list):
                for event in resp:
                    title = event.get('title', '')
                    slug = event.get('slug', '')
                    
                    # Target only the specific high-temperature patterns
                    if "temperature" in slug or "highest-temperature" in title.lower():
                        print(f"✅ Found Market: {title}")
                        ticker = event.get('ticker', '')
                        if ticker:
                            res = get_market_data_for_city(ticker)
                            if "🔍 ANALYSIS" in res:
                                requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", 
                                              data={"chat_id": config.TELEGRAM_CHAT_ID, "text": res, "parse_mode": "Markdown"})
            else:
                print("API error: Response is not a list.")
        except Exception as e:
            print(f"Background error: {e}")
            
        print("💤 Scan complete. Waiting 15 minutes...")
        time.sleep(900)

if __name__ == "__main__":
    threading.Thread(target=handle_commands, daemon=True).start()
    background_scan()
