"""Global configuration and strategy parameters."""

# API Credentials
TELEGRAM_BOT_TOKEN = "8338861744:AAEhvJfvwqcsVTdKX6ZscrXzvT2acfXTH3U"
TELEGRAM_CHAT_ID = 8748661170

"""Global configuration and strategy parameters."""

TELEGRAM_BOT_TOKEN = "8338861744:AAEhvJfvwqcsVTdKX6ZscrXzvT2acfXTH3U"
TELEGRAM_CHAT_ID = 8748661170

# Updated Weights including HRRR[cite: 6, 9]
# HRRR is weighted highest for <18 hour lookaheads
# Updated Weights for 2026 Strategy[cite: 6, 9]
WEIGHTS = {
    "HRRR": 0.45,       # High-res rapid refresh (Best for <18 hours)
    "ECMWF": 0.25,      # European Model
    "GFS": 0.20,        # American Model
    "GRAPHCAST": 0.10   # AI Model consensus
}
