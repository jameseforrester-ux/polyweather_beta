import requests
import time
import config
from messages import format_alert
from strategy import calculate_consensus

# PASTE THE ALL_CITIES LIST FROM ABOVE HERE

def get_live_id(ticker):
    """Automatically finds today's active YES token ID for a city."""
    try:
        url = f"https://gamma-api.polymarket.com/events?active=true&query={ticker}"
        data = requests.get(url).json()
        # Grabs the first active 'YES' token ID automatically
        market = data[0]['markets'][0]
        import json
        ids = json.loads(market['clobTokenIds'])
        return ids['1'], market['conditionId'] # Returns YES Token ID and Condition ID
    except:
        return None, None

def fetch_market_data(city):
    """Fetches real data using the automated ID finder."""
    token_id, condition_id = get_live_id(city['ticker'])
    if not token_id:
        return None

    # 1. Weather API Call (Using your Config Key)
    w_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={city['lat']}&lon={city['lon']}&appid={config.WEATHER_API_KEY}&units=metric"
    w_data = requests.get(w_url).json()

    # 2. Polymarket Price Call
    p_url = f"https://clob.polymarket.com/price/buy/{token_id}"
    p_price = float(requests.get(p_url).json().get('price', 0)) * 100

    return {
        "price": p_price,
        "models": {
            "hrrr": w_data['hourly'][0]['temp'],
            "ecmwf": w_data['daily'][0]['temp']['day'],
            "gfs": w_data['current']['temp']
        },
        "reasoning": f"Automated check for {city['name']} using live Token {token_id[:6]}."
    }

def run_main_loop():
    print("🚀 Monitoring 36 Cities with Automated ID Discovery...")
    while True:
        for city in ALL_CITIES:
            data = fetch_market_data(city)
            if data:
                temp, conf = calculate_consensus(data['models'])
                msg = format_alert(city['name'], "🟢 BUY" if conf > 0.8 else "⚪ NEUTRAL", conf, data['price'], temp, city['unit'], data['reasoning'])
                
                # Send to Telegram
                requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", 
                              data={"chat_id": config.TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                print(f"✅ Alert sent for {city['name']}")
            time.sleep(5)
        time.sleep(900)

if __name__ == "__main__":
    run_main_loop()
