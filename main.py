# Example of how to call the new message function
formatted_msg = format_alert(
    city_name="New York",
    signal="🟢 STRONG BUY",
    confidence=0.82,
    price=32,
    temp=74.5, # The consensus value
    unit="F",  # Or "C" depending on the market[cite: 8]
    analysis="HRRR and ECMWF both show a 2-degree spike above market average."
)
