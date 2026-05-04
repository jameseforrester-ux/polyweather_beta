"""Calculates confidence and suggests trade actions."""
import config

def to_celsius(f): 
    """Converts Fahrenheit to Celsius for international markets[cite: 10]."""
    return (f - 32) * 5/9

def to_fahrenheit(c): 
    """Converts Celsius to Fahrenheit for US markets[cite: 10]."""
    return (c * 9/5) + 32

def format_temp(temp, unit="F"):
    """Ensures the alert matches the market's specific unit[cite: 8]."""
    if unit.upper() == "C":
        return f"{temp:.1f}°C"
    return f"{temp:.1f}°F"

import config

def calculate_consensus(model_outputs: dict) -> float:
    """Calculates weighted confidence score[cite: 6]."""
    score = 0.0
    for model, prob in model_outputs.items():
        score += prob * config.WEIGHTS.get(model, 0)
    return score

def get_trade_signal(confidence: float, market_price: float):
    """
    Determines if the edge is sufficient to trade.
    Formula: Edge = Confidence - Market Implied Probability[cite: 9, 11].
    """
    edge = confidence - market_price
    
    if edge > 0.15 and confidence >= config.MIN_CONFIDENCE:
        return "🟢 STRONG BUY", "High Edge detected vs Market"
    elif edge > 0.05:
        return "🟡 LEAN BUY", "Moderate edge; consider small position"
    elif edge < -0.10:
        return "🔴 EXIT / SHORT", "Market is overpricing this outcome"
    return "⚪ HOLD", "No significant edge"
