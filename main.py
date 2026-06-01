import asyncio
from aiohttp import web
from config import TELEGRAM_BOT_TOKEN, SYMBOLS, ADMIN_CHAT_ID
from data_feeds import MarketData
from signal_generator import SignalGenerator
from trade_manager import TradeManager
from beast_engine.adaptive_learner import init_db
import bot_handlers

async def health_check(request):
    return web.Response(text="OK")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Health check server started on port 8080")

async def main():
    init_db()
    md = MarketData(SYMBOLS)
    asyncio.create_task(md.twelvedata_ws())

    sig_gen = SignalGenerator(md)
    await sig_gen.update_sentiment()

    bot = bot_handlers.TradingBot(TELEGRAM_BOT_TOKEN, sig_gen, md)
    tm = TradeManager(md, bot)

    async def scan_loop():
        while True:
            for sym in SYMBOLS:
                try:
                    signal = await sig_gen.evaluate_symbol(sym)
                    if signal:
                        await tm.open_trade(signal)
                except Exception as e:
                    print(f"Error evaluating {sym}: {e}")
            await asyncio.sleep(30)

    asyncio.create_task(scan_loop())
    asyncio.create_task(tm.monitor_trades())
    asyncio.create_task(run_web_server())

    async with bot.app:
    await bot.app.start()
    print("Bot polling started")
    # تشغيل البولينج (يغني عن updater)
    await bot.app.updater.start_polling()   # 👈 غلط، امسح هذا السطر
    # استخدم هذا بداله:
    await bot.app.run_polling()             # 👈 هذا الصحيح

if __name__ == "__main__":
    asyncio.run(main())
