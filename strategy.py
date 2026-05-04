"""Calculates confidence and suggests trade actions."""
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
