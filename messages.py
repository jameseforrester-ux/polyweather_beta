"""Formatters for Telegram alerts."""

def format_alert(city_name, signal, confidence, price, analysis):
    """Creates a professional dashboard-style alert[cite: 3]."""
    bar_length = int(confidence * 10)
    progress_bar = "█" * bar_length + "░" * (10 - bar_length)
    
    template = (
        f"📊 *Weather Market Update: {city_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Signal: {signal}\n"
        f"Confidence: {progress_bar} {confidence:.1%}\n"
        f"Market Price: {price}¢\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 *Analysis:* {analysis}\n"
    )
    return template
