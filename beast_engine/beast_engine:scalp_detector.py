def detect_scalp_setup(df_1m, df_5m):
    if len(df_5m) < 20 or len(df_1m) < 5:
        return None
    last_5m = df_5m.iloc[-1]
    atr_5m = last_5m['ATR']
    if atr_5m == 0:
        return None
    recent_high = df_5m['high'].iloc[-10:-1].max()
    recent_low = df_5m['low'].iloc[-10:-1].min()
    range_ratio = (recent_high - recent_low) / atr_5m
    if range_ratio > 1.5:
        return None
    last_1m = df_1m.iloc[-1]
    if len(df_1m) >= 2:
        prev_1m = df_1m.iloc[-2]
    else:
        return None
    vol_avg_1m = df_1m['volume'].rolling(20).mean().iloc[-1]
    if (last_1m['close'] > recent_high and
        last_1m['close'] > last_1m['open'] and
        last_1m['volume'] > 3 * vol_avg_1m and
        last_1m['RSI'] > 55):
        entry = last_1m['close'] * 1.001
        stop = entry - (atr_5m * 0.5)
        target1 = entry + (atr_5m * 1.2)
        target2 = entry + (atr_5m * 2)
        return {"entry": entry, "stop": stop, "target1": target1, "target2": target2, "type": "SCALP"}
    return None