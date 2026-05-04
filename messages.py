"""Formatters for Telegram alerts."""

def format_alert(city_name, signal, confidence, price, temp, unit, analysis):
    """Creates the scannable dashboard for Telegram[cite: 3]."""
    # Create the visual bar: █ for filled, ░ for empty[cite: 3]
    bar_length = int(confidence * 10)
    progress_bar = "█" * bar_length + "░" * (10 - bar_length)
    
    return (
        f"🌡️ *Target: {city_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Consensus Temp: {temp}°{unit}\n"
        f"Signal: {signal}\n"
        f"Confidence: {progress_bar} {confidence:.1%}\n"
        f"Market Price: {price}¢\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 *Edge:* {analysis}\n"
    )
