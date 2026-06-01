import asyncio
from datetime import datetime, timedelta
from data_feeds import MarketData
from beast_engine.adaptive_learner import record_trade

class TradeManager:
    def __init__(self, market_data: MarketData, bot):
        self.md = market_data
        self.bot = bot
        self.active_trades = []
        self.daily_pnl = 0

    async def open_trade(self, signal):
        conf = signal['confidence']
        if conf >= 9:
            risk_pct = 0.04
        elif conf >= 7:
            risk_pct = 0.02
        else:
            risk_pct = 0.01
        account = 10000
        risk_amount = account * risk_pct
        stop_distance = abs(signal['entry'] - signal['stop'])
        if stop_distance == 0:
            return
        shares = risk_amount / stop_distance
        trade = {
            'symbol': signal['symbol'],
            'entry': signal['entry'],
            'stop': signal['stop'],
            'target1': signal['target1'],
            'target2': signal['target2'],
            'shares': shares,
            'confidence': conf,
            'type': signal['type'],
            'open_time': datetime.now(),
            'half_closed': False
        }
        self.active_trades.append(trade)
        await self.send_alert(trade, "OPEN")

    async def monitor_trades(self):
        while True:
            await asyncio.sleep(1)
            for trade in self.active_trades[:]:
                symbol = trade['symbol']
                price_tuple = self.md.prices.get(symbol)
                if not price_tuple:
                    continue
                current = price_tuple[1]
                if current <= trade['stop']:
                    pnl = (current - trade['entry']) * trade['shares']
                    record_trade(symbol, trade['entry'], current, 'LONG', pnl, trade['confidence'], 'STOP_LOSS')
                    await self.send_alert(trade, "STOP_LOSS", exit_price=current)
                    self.active_trades.remove(trade)
                    continue
                if not trade['half_closed'] and current >= trade['target1']:
                    half_shares = trade['shares'] / 2
                    pnl1 = (trade['target1'] - trade['entry']) * half_shares
                    trade['shares'] /= 2
                    trade['stop'] = trade['entry']
                    trade['half_closed'] = True
                    await self.send_alert(trade, "TARGET1", exit_price=trade['target1'])
                if trade['half_closed'] and current >= trade['target2']:
                    pnl2 = (current - trade['entry']) * trade['shares']
                    record_trade(symbol, trade['entry'], current, 'LONG', pnl2, trade['confidence'], 'TARGET2')
                    await self.send_alert(trade, "TARGET2", exit_price=current)
                    self.active_trades.remove(trade)
                    continue
                if datetime.now() - trade['open_time'] > timedelta(days=7):
                    pnl = (current - trade['entry']) * trade['shares']
                    record_trade(symbol, trade['entry'], current, 'LONG', pnl, trade['confidence'], 'TIME_EXIT')
                    await self.send_alert(trade, "TIME_EXIT", exit_price=current)
                    self.active_trades.remove(trade)

    async def send_alert(self, trade, event, exit_price=None):
        from config import ADMIN_CHAT_ID
        msg = ""
        if event == "OPEN":
            extra = "💎" if trade['confidence'] >= 9 else ("🔥" if trade['confidence'] >=7 else "")
            msg = f"{extra} {trade['type']} شراء {trade['symbol']}\nسعر الدخول: {trade['entry']:.2f}\n⛔ وقف: {trade['stop']:.2f}\n🎯 هدف1: {trade['target1']:.2f} | هدف2: {trade['target2']:.2f}\n⚡ الثقة: {trade['confidence']}/10"
        else:
            pnl_str = "ربح" if exit_price > trade['entry'] else "خسارة"
            msg = f"✅ {trade['symbol']} خرج {event}: {pnl_str} @ {exit_price:.2f}"
        await self.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)