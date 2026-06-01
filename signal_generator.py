import asyncio
import pandas as pd
from data_feeds import MarketData
from indicators import add_all_indicators, add_emas
from beast_engine.scalp_detector import detect_scalp_setup
from beast_engine.option_flow import check_unusual_options
from beast_engine.confidence_scorer import calculate_confidence
from beast_engine.adaptive_learner import learn_patterns
from config import SYMBOLS

class SignalGenerator:
    def __init__(self, market_data: MarketData):
        self.md = market_data
        self.premarket_mood = "RISK-ON"
        self.premarket_sector = "ALL"
        self.learned_rules = {}

    async def update_sentiment(self):
        from beast_engine.sentiment_premarket import premarket_sentiment
        self.premarket_mood, self.premarket_sector = await premarket_sentiment()

    async def analyze_news(self, headlines):
        if not headlines:
            return 3
        from anthropic import Anthropic
        from config import ANTHROPIC_API_KEY
        anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"حلل هذه العناوين وأعط تقييماً من 1 (سلبي جداً) إلى 5 (إيجابي جداً):\n" + "\n".join(headlines) + "\nأجب برقم فقط."
        resp = anthropic.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=5,
            messages=[{"role":"user","content":prompt}]
        )
        try:
            return int(resp.content[0].text.strip())
        except:
            return 3

    async def evaluate_symbol(self, symbol):
        df_15 = await self.md.get_historical_candles(symbol, '15min', 100)
        df_1h = await self.md.get_historical_candles(symbol, '1h', 100)
        df_1m = await self.md.get_historical_candles(symbol, '1min', 60)
        df_5m = await self.md.get_historical_candles(symbol, '5min', 60)
        if df_15.empty or df_1h.empty:
            return None

        df_15 = add_all_indicators(df_15)
        df_1h = add_emas(df_1h, [20,50])
        df_1h = add_all_indicators(df_1h)  # لإضافة VWAP وغيره
        df_1m = add_all_indicators(df_1m)
        df_5m = add_all_indicators(df_5m)

        # سكالب
        if self.premarket_mood != "RISK-OFF":
            scalp_signal = detect_scalp_setup(df_1m, df_5m)
            if scalp_signal:
                opt_flow = await check_unusual_options(symbol)
                conf = calculate_confidence(4, opt_flow, scalp=True, sentiment_mood=self.premarket_mood)
                scalp_signal['confidence'] = conf
                scalp_signal['symbol'] = symbol
                return scalp_signal

        # سوينق
        last_15 = df_15.iloc[-1]
        last_1h = df_1h.iloc[-1]
        trend_up = last_1h['EMA20'] > last_1h['EMA50'] and last_1h['close'] > last_1h['VWAP']
        rsi_ok = 45 < last_15['RSI'] < 72
        macd_ok = last_15['MACD_line'] > last_15['MACD_signal']
        vol_ok = last_15['vol_ratio'] > 1.5

        # اختراق
        df_today = df_15[df_15['date'].dt.date == pd.Timestamp.now().date()]
        today_high = df_today['high'].max() if not df_today.empty else last_15['close']
        breakout = last_15['close'] > today_high and last_15['close'] > last_15['open']
        vwap_bounce = (last_15['low'] <= last_15['VWAP'] <= last_15['close']) and vol_ok
        price_action_ok = (breakout or vwap_bounce)
        extra_conf = last_15['bull_engulf'] or last_15['CMF'] > 0

        if 'RSI_MAX' in self.learned_rules and last_15['RSI'] > 72:
            return None

        base_score = sum([trend_up, rsi_ok and macd_ok, vol_ok and price_action_ok, extra_conf])
        headlines = await self.md.get_news(symbol)
        news_score = await self.analyze_news(headlines)
        if news_score >= 4:
            base_score += 1

        opt_score = await check_unusual_options(symbol)
        conf = calculate_confidence(base_score, opt_score, scalp=False, sentiment_mood=self.premarket_mood)

        if (base_score >= 4 and conf >= 7) or (base_score >= 3 and opt_score >= 2):
            atr = last_15['ATR']
            entry = last_15['close'] * 1.001
            stop = entry - (atr * 0.7)
            target1 = entry + (atr * 1.8)
            target2 = entry + (atr * 3.2)
            return {
                "symbol": symbol,
                "entry": entry,
                "stop": stop,
                "target1": target1,
                "target2": target2,
                "type": "SWING",
                "confidence": conf
            }
        return None
