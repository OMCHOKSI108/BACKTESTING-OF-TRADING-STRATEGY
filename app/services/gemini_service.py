def parse_strategy(strategy_text):
    # In real usage, call Gemini API here.
    # For now, mock "RSI < 30, RSI > 70"
    return {"type": "RSI", "buy": 30, "sell": 70}
