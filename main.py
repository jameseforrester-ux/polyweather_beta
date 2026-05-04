import requests
import time
import config
from messages import format_alert
from strategy import calculate_consensus, format_temp

# 1. Define your 36 cities (Add the rest of your list here)
ALL_CITIES = [
    {"name": "New York", "unit": "F", "market_id": "poly-123"},
    {"name": "Chicago", "unit": "F", "market_id": "poly-456"},
    {"name": "London", "unit": "C", "market_id": "poly-789"},
    # ... add all 36 cities from your sheet
]

def fetch_market_data(city):
    """Placeholder: Replace with your actual API calls to Polymarket/Weather APIs"""
    # This is where your code gets real prices and model temps
    return {
        "price": 45, 
        "models": {"hrrr": 72.5, "ecmwf": 71.0, "gfs": 73.0},
        "reasoning": "HRRR showing warm bias in lower Manhattan."
    }

def run_main_loop():
    print("🚀 Starting PolyWeather Full Monitoring...")
    
    while True:
        for city_data in ALL_CITIES:
            try:
                # 1. Get fresh data
                data = fetch_market_data(city_data)
                
                # 2. Use your strategy logic to find consensus
                consensus_temp, confidence = calculate_consensus(data['models'])
                
                # 3. Format the alert using your new message template
                formatted_msg = format_alert(
                    city_name=city_data['name'],
                    signal="🟢 BUY" if confidence > 0.7 else "⚪ NEUTRAL",
                    confidence=confidence,
                    price=data['price'],
                    temp=consensus_temp,
                    unit=city_data['unit'],
                    analysis=data['reasoning']
                )

                # 4. Send to Telegram
                url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": formatted_msg, "parse_mode": "Markdown"}
                requests.post(url, data=payload)
                
                print(f"✅ Alert sent for {city_data['name']}")
                time.sleep(2) # Brief pause between cities to avoid rate limits

            except Exception as e:
                print(f"❌ Error processing {city_data['name']}: {e}")

        print("💤 Full cycle complete. Sleeping for 15 minutes...")
        time.sleep(900) # Wait 15 mins before checking all cities again

if __name__ == "__main__":
    run_main_loop()
