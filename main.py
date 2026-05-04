import requests
import config
from messages import format_alert
from strategy import calculate_consensus, format_temp

# --- START OF BOT LOGIC ---

# 1. Verification Block (This ensures the bot stays alive and alerts you)
try:
    test_city = "System Check"
    test_unit = "F" # You can change this to "C" to test your new logic

    formatted_msg = format_alert(
        city_name=test_city,
        signal="⚪ SYSTEM START",
        confidence=1.0,
        price=0,
        temp=72.0,
        unit=test_unit,
        analysis="HRRR Model & Unit Conversion Logic initialized successfully."
    )

    # Sending the "I am alive" message to Telegram
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": formatted_msg,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, data=payload)
    print(f"Startup Status: {response.status_code}")

except Exception as e:
    print(f"Startup Error: {e}")


# 2. Main Processing Loop (Placeholder for your city tracking)
def run_main_loop():
    # This is where your for-loop for ALL_CITIES will eventually go.
    # We use 'city_data' inside the loop to avoid NameErrors.
    print("Bot is now monitoring markets...")

if __name__ == "__main__":
    run_main_loop()
