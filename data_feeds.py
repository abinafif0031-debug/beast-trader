import asyncio
import aiohttp
import websockets
import json
import pandas as pd
from datetime import datetime
from config import TWELVE_DATA_KEY, ALPHA_VANTAGE_KEY, FINNHUB_API_KEY
import finnhub

SYMBOLS = []  # سيتم تعبئته من main

class MarketData:
    def __init__(self, symbols):
        self.symbols = symbols
        self.prices = {}
        self.candles_1m = {}
        self.candles_5m = {}
        self.candles_15m = {}
        self.candles_1h = {}
        self.condition = asyncio.Condition()

    async def twelvedata_ws(self):
        url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={TWELVE_DATA_KEY}"
        async with websockets.connect(url) as ws:
            subscribe = {
                "action": "subscribe",
                "params": {"symbols": ",".join(self.symbols)}
            }
            await ws.send(json.dumps(subscribe))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("event") == "price":
                    symbol = data["symbol"]
                    price = float(data["price"])
                    timestamp = data["timestamp"]
                    self.prices[symbol] = (timestamp, price)
                    # هنا يمكن تحديث الشموع ولكن للتبسيط سنكتفي بالسعر
                    async with self.condition:
                        self.condition.notify_all()

    async def get_historical_candles(self, symbol, interval='15min', outputsize=100):
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if 'values' not in data:
                    return pd.DataFrame()
                df = pd.DataFrame(data['values'])
                df = df.rename(columns={'datetime':'date','open':'open','high':'high','low':'low','close':'close','volume':'volume'})
                df['date'] = pd.to_datetime(df['date'])
                df.sort_values('date', inplace=True)
                for col in ['open','high','low','close','volume']:
                    df[col] = df[col].astype(float)
                return df

    async def get_spy_trend(self):
        url = f"https://www.alphavantage.co/query?function=EMA&symbol=SPY&interval=daily&time_period=50&series_type=close&apikey={ALPHA_VANTAGE_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                try:
                    last_ema = float(list(data['Technical Analysis: EMA'].values())[0]['EMA'])
                    return last_ema
                except:
                    return None

    async def get_news(self, symbol):
        try:
            finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
            news = finnhub_client.company_news(symbol, _from="2024-01-01", to="2024-12-31")
            headlines = [n['headline'] for n in news[:5]]
            return headlines
        except:
            return []