"""Global configuration and strategy parameters."""

# API Credentials
TELEGRAM_BOT_TOKEN = "8338861744:AAEhvJfvwqcsVTdKX6ZscrXzvT2acfXTH3U"
TELEGRAM_CHAT_ID = 8748661170

# Strategy Weights for Consensus
# Assigns importance to different weather models[cite: 6, 9]
WEIGHTS = {
    "ECMWF": 0.40,      # Euro model (high reliability)
    "GFS": 0.30,        # US Global model
    "GRAPHCAST": 0.20,  # AI/Machine Learning model
    "HISTORICAL": 0.10  # Climatology baseline
}

# Trade Thresholds
MIN_CONFIDENCE = 0.65  # Only alert if >65% certain[cite: 11]
ENTRY_WINDOW_HOURS = 24 # Lookahead window for weather events
