import time
import requests
from metar import Metar
from telegram import Bot
import asyncio
import datetime

# --- CONFIGURATION ---
# 1. Get your token from @BotFather on Telegram
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
# 2. Get your ID from @userinfobot on Telegram
USER_ID = "YOUR_CHAT_ID_HERE"

# Airport ICAO codes to monitor (Polymarket usually uses major US hubs)
MONITORED_AIRPORTS = ["KORD", "KJFK", "KLAX", "KDEN", "KATL", "KPHX", "KMIA", "KSFO"]

bot = Bot(token=TELEGRAM_TOKEN)

def get_metar_temp(icao):
    """
    Fetch raw METAR from NOAA Aviation Weather Center.
    This is the fastest source, bypassing Weather Underground's cache.
    """
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao}.TXT"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.splitlines()
            # The second line contains the METAR string
            raw_metar = lines[1]
            obs = Metar.Metar(raw_metar)
            temp_c = obs.temp.value()
            temp_f = (temp_c * 9/5) + 32
            return round(temp_f, 2)
    except Exception as e:
        print(f"Error fetching METAR for {icao}: {e}")
    return None

async def send_alert(message):
    try:
        await bot.send_message(chat_id=USER_ID, text=message, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

async def main_loop():
    print(f"[{datetime.datetime.now()}] Bot Initialized. Monitoring {len(MONITORED_AIRPORTS)} airports...")
    
    # Track last alerted temp to avoid spamming the same degree
    last_reported_temps = {icao: 0 for icao in MONITORED_AIRPORTS}

    while True:
        try:
            for icao in MONITORED_AIRPORTS:
                current_temp = get_metar_temp(icao)
                
                if current_temp:
                    # Logic: Alert if temp changes by 1 degree or more since last alert
                    diff = abs(current_temp - last_reported_temps[icao])
                    
                    if diff >= 1.0:
                        alert_msg = (
                            f"🌡️ *TEMPERATURE EDGE: {icao}*\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"*Real-Time METAR:* {current_temp}°F\n"
                            f"*Status:* Trend Shift Detected (+/- 1°)\n\n"
                            f"⚠️ *Action:* Check Weather Underground lag vs Polymarket order book now."
                        )
                        await send_alert(alert_msg)
                        last_reported_temps[icao] = current_temp
                        print(f"Alert sent for {icao}: {current_temp}F")
                
                await asyncio.sleep(2)

        except Exception as e:
            print(f"Error in main loop: {e}")
            
        # Check every 5 minutes (300 seconds)
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main_loop())
