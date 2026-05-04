# Example of how to call the new message function
from messages import format_alert
from strategy import calculate_consensus, format_temp

# Example placement inside your main loop
msg = format_alert(
    city_name=city_data['name'],
    signal=signal_type,
    confidence=conf_score,
    price=current_price,
    temp=consensus_temp,  # New variable from strategy.py
    unit=city_data['unit'], # 'F' or 'C'
    analysis=reasoning
)
