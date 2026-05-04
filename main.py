# Example of how to call the new message function
from messages import format_alert
from strategy import calculate_consensus, format_temp

# --- REPLACEMENT BLOCK START ---
test_city = "New York"
test_unit = "F"

formatted_msg = format_alert(
    city_name=test_city,
    signal="⚪ SYSTEM START",
    confidence=0.99,
    price=0,
    temp=70.0,
    unit=test_unit,
    analysis="Bot restarted successfully. HRRR weights active."
)

print(formatted_msg) 
# --- REPLACEMENT BLOCK END ---
