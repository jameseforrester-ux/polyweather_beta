"""Global configuration and strategy parameters."""

# API Credentials
TELEGRAM_BOT_TOKEN = "8338861744:AAEhvJfvwqcsVTdKX6ZscrXzvT2acfXTH3U"
TELEGRAM_CHAT_ID = 8748661170

"""Global configuration and strategy parameters."""

TELEGRAM_BOT_TOKEN = "8338861744:AAEhvJfvwqcsVTdKX6ZscrXzvT2acfXTH3U"
TELEGRAM_CHAT_ID = 8748661170

# Updated Weights including HRRR[cite: 6, 9]
# HRRR is weighted highest for <18 hour lookaheads
WEIGHTS = {
    "HRRR": 0.45,       # High-res rapid refresh (US Only)
    "ECMWF": 0.25,      # Euro Global
    "GFS": 0.20,        # US Global
    "GRAPHCAST": 0.10   # AI model
}

MIN_CONFIDENCE = 0.65
