#!/usr/bin/env python3
"""Dynamic Take-Profit and Stop-Loss Calculator

Instead of one-size-fits-all (35% TP, 25% SL), this calculates optimal targets
based on coin characteristics:
- Volatility (higher volatility = wider stops)
- Score (higher score = more aggressive targets)
- Market Cap (smaller = higher risk = wider stops)
- Volume (weaker volume = tighter stops)
"""


def calculate_dynamic_targets(coin_data: dict) -> tuple:
    """Calculate optimal TP and SL percentages for a coin

    Args:
        coin_data: Dict with coin metrics (score, market_cap, volume_change_24h, etc.)

    Returns:
        (take_profit_pct, stop_loss_pct) as decimals (e.g. 0.35 = 35%)
    """

    # Base targets (CONSERVATIVE - shitcoins pump fast then dump)
    base_tp = 0.15  # 15% - take profits quick!
    base_sl = 0.15  # 15% - tight risk management

    # Factor 1: SCORE (Higher score = slightly more aggressive TP, tighter SL)
    score = coin_data.get('enhanced_score', 70)
    if score >= 85:
        # Very high confidence → can aim a bit higher
        tp_multiplier = 1.2  # 18% TP
        sl_multiplier = 0.9  # 13.5% SL (tighter)
    elif score >= 75:
        # High confidence → standard
        tp_multiplier = 1.1  # 16.5% TP
        sl_multiplier = 1.0  # 15% SL
    elif score >= 65:
        # Medium confidence → conservative
        tp_multiplier = 1.0  # 15% TP
        sl_multiplier = 1.1  # 16.5% SL
    else:
        # Lower confidence → very conservative
        tp_multiplier = 0.8  # 12% TP
        sl_multiplier = 1.2  # 18% SL (wider)

    # Factor 2: MARKET CAP (Smaller = higher volatility = wider stops)
    market_cap = coin_data.get('market_cap', 50_000_000)
    if market_cap < 40_000_000:
        # Small cap → very volatile → wider stops
        sl_multiplier *= 1.2  # +20% wider SL
        tp_multiplier *= 1.1  # +10% higher TP
    elif market_cap > 200_000_000:
        # Larger cap → less volatile → tighter stops
        sl_multiplier *= 0.9  # -10% tighter SL
        tp_multiplier *= 0.95  # -5% lower TP

    # Factor 3: VOLUME MOMENTUM (Strong volume = hold longer)
    volume_change = coin_data.get('volume_change_24h', 50)
    if volume_change > 100:
        # Very strong momentum → hold for bigger gains
        tp_multiplier *= 1.15  # +15% higher TP
    elif volume_change < 40:
        # Weak momentum → exit faster
        tp_multiplier *= 0.9  # -10% lower TP
        sl_multiplier *= 0.9  # -10% tighter SL (exit bad setups faster)

    # Factor 4: RECENT PUMP (Already pumped = tighter TP)
    change_24h = coin_data.get('change_24h', 5)
    if change_24h > 12:
        # Already pumped significantly → take profits faster
        tp_multiplier *= 0.85  # -15% lower TP (don't be greedy!)
    elif change_24h < 3:
        # Fresh, not pumped → can hold longer
        tp_multiplier *= 1.1  # +10% higher TP

    # Calculate final targets
    take_profit_pct = base_tp * tp_multiplier
    stop_loss_pct = base_sl * sl_multiplier

    # Safety caps (prevent extreme values - keep it REALISTIC for shitcoins)
    take_profit_pct = min(max(take_profit_pct, 0.10), 0.25)  # 10-25%
    stop_loss_pct = min(max(stop_loss_pct, 0.10), 0.25)  # 10-25%

    return (take_profit_pct, stop_loss_pct)


def explain_targets(coin_data: dict) -> str:
    """Generate explanation for why these targets were chosen

    Args:
        coin_data: Dict with coin metrics

    Returns:
        Human-readable explanation
    """
    tp, sl = calculate_dynamic_targets(coin_data)

    score = coin_data.get('enhanced_score', 70)
    mcap = coin_data.get('market_cap', 50_000_000)
    vol = coin_data.get('volume_change_24h', 50)
    pump = coin_data.get('change_24h', 5)

    explanation = []

    # Score reasoning
    if score >= 85:
        explanation.append(f"⭐ Very high score ({score}) → Aggressive +{tp*100:.0f}% TP")
    elif score >= 75:
        explanation.append(f"✅ High score ({score}) → Standard targets")
    else:
        explanation.append(f"⚠️ Medium score ({score}) → Conservative targets")

    # Market cap reasoning
    if mcap < 40_000_000:
        explanation.append(f"💎 Small cap (${mcap/1e6:.1f}M) → Wider -{sl*100:.0f}% SL")
    elif mcap > 200_000_000:
        explanation.append(f"🏢 Large cap (${mcap/1e6:.1f}M) → Tighter -{sl*100:.0f}% SL")

    # Volume reasoning
    if vol > 100:
        explanation.append(f"🚀 Strong volume (+{vol:.0f}%) → Hold for +{tp*100:.0f}%")
    elif vol < 40:
        explanation.append(f"📉 Weak volume (+{vol:.0f}%) → Quick exit")

    # Pump reasoning
    if pump > 12:
        explanation.append(f"⚠️ Already pumped (+{pump:.1f}%) → Take profits at +{tp*100:.0f}%")
    elif pump < 3:
        explanation.append(f"🆕 Fresh entry (+{pump:.1f}%) → Can target +{tp*100:.0f}%")

    return "\n".join(explanation)


# Example usage
if __name__ == "__main__":
    # Example 1: High-quality small cap
    coin1 = {
        'enhanced_score': 87,
        'market_cap': 35_000_000,
        'volume_change_24h': 120,
        'change_24h': 8
    }

    tp1, sl1 = calculate_dynamic_targets(coin1)
    print("Example 1: High-quality small cap gem")
    print(f"TP: {tp1*100:.1f}%, SL: {sl1*100:.1f}%")
    print(explain_targets(coin1))
    print()

    # Example 2: Already pumped mid-score coin
    coin2 = {
        'enhanced_score': 72,
        'market_cap': 80_000_000,
        'volume_change_24h': 45,
        'change_24h': 18
    }

    tp2, sl2 = calculate_dynamic_targets(coin2)
    print("Example 2: Already pumped mid-score coin")
    print(f"TP: {tp2*100:.1f}%, SL: {sl2*100:.1f}%")
    print(explain_targets(coin2))
    print()

    # Example 3: Low-quality weak setup
    coin3 = {
        'enhanced_score': 68,
        'market_cap': 150_000_000,
        'volume_change_24h': 32,
        'change_24h': 5
    }

    tp3, sl3 = calculate_dynamic_targets(coin3)
    print("Example 3: Low-quality weak setup")
    print(f"TP: {tp3*100:.1f}%, SL: {sl3*100:.1f}%")
    print(explain_targets(coin3))
