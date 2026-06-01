def calculate_confidence(base_score, opt_flow_score, scalp=False, sentiment_mood="RISK-ON"):
    conf = base_score * 1.5
    conf += opt_flow_score * 0.8
    if scalp:
        conf += 0.5
    if sentiment_mood == "RISK-ON":
        conf += 0.5
    elif sentiment_mood == "RISK-OFF":
        conf -= 1
    return max(1, min(10, round(conf)))