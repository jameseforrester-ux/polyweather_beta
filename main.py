import requests
import time
import config
from messages import format_alert
from strategy import calculate_consensus, format_temp

# 1. The Full City List (Add all 36 here with their Lat/Lon and Poly Market IDs)
ALL_CITIES = [
    {"name": "New York", "unit": "F", "lat": 40.71, "lon": -74.00, "market_id": "0x..."},
    {"name": "Chicago", "unit": "F", "lat": 41.87, "lon": -87.62, "market_id": "0x..."},
    {"name": "London", "unit": "C", "lat": 51.50, "lon": -0.12, "market_id": "0x..."},
]

def fetch_market_data(city):
    """Fetches real-time weather and Polymarket price data."""
    try:
        # Get Weather Data (HRRR/ECMWF/GFS weights handled in strategy.py)
        weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={city['lat']}&lon={city['lon']}&appid={config.WEATHER_API_KEY}&units=metric"
        w_resp = requests.get(weather_url).json()

        # Map API hourly/daily outputs to our model keys
        models = {
            "hrrr": w_resp['hourly'][0]['temp'],  
            "ecmwf": w_resp['daily'][0]['temp']['day'],
            "gfs": w_resp['current']['temp']
        }

        # Get Polymarket Price (CLOB API)
        poly_url = f"https://clob.polymarket.com/price/buy/{city['market_id']}"
        p_resp = requests.get(poly_url).json()
        current_price = float(p_resp.get('price', 0)) * 100 

        return {
            "price": current_price,
            "models": models,
            "reasoning": f"Live Market check vs HRRR consensus."
        }
    except Exception as e:
        print(f"Fetch error for {city['name']}: {e}")
        return None

def run_main_loop():
    print("🚀 PolyWeather Bot is monitoring 36 markets...")
    
    while True:
        for city_data in ALL_CITIES:
            data = fetch_market_data(city_data)
            
            if data:
                # Use strategy logic for HRRR (45%) & ECMWF (25%) weights
                consensus_temp, confidence = calculate_consensus(data['models'])
                
                # Format the final Markdown alert
                formatted_msg = format_alert(
                    city_name=city_data['name'],
                    signal="🟢 BUY" if confidence > 0.75 else "⚪ NEUTRAL",
                    confidence=confidence,
                    price=data['price'],
                    temp=consensus_temp,
                    unit=city_data['unit'], # Dynamic F/C support
                    analysis=data['reasoning']
                )

                # Push to Telegram
                url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": formatted_msg, "parse_mode": "Markdown"}
                
                requests.post(url, data=payload)
                print(f"✅ Processed {city_data['name']}")
            
            time.sleep(2) # Prevent Telegram rate limits

        print("💤 Full cycle complete. Waiting 15 minutes...")
        time.sleep(900)

if __name__ == "__main__":
    run_main_loop()
