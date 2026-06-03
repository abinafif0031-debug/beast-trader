import asyncio
import logging
from aiohttp import web
from config import TELEGRAM_BOT_TOKEN, SYMBOLS, ADMIN_CHAT_ID
from data_feeds import MarketData
from signal_generator import SignalGenerator
from trade_manager import TradeManager
from beast_engine.adaptive_learner import init_db
import bot_handlers

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== دالة اختبار كلود (مؤقتة) ==========
async def test_claude_model():
    from anthropic import Anthropic
    from config import ANTHROPIC_API_KEY
    anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    models_to_try = [
        "claude-3-haiku-20240307",
        "claude-3-5-haiku-20241022",
        "claude-3-5-haiku-latest",
        "claude-3-opus-20240229",
    ]
    for model in models_to_try:
        try:
            resp = anthropic.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role":"user","content":"Say test"}]
            )
            logger.info(f"✅ النموذج الشغال: {model}")
            return model
        except Exception as e:
            logger.warning(f"❌ {model}: {e}")
    return None
# =============================================

async def health_check(request):
    return web.Response(text="OK")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Health check server started on port 8080")

async def safe_twelvedata_ws(md):
    while True:
        try:
            await md.twelvedata_ws()
        except Exception as e:
            logger.error(f"Twelve Data WebSocket انقطع: {e}")
            await asyncio.sleep(5)

async def main():
    init_db()
    logger.info("قاعدة البيانات جاهزة")

    # 🔍 اختبر النموذج أولاً
    model_name = await test_claude_model()
    if model_name:
        logger.info(f"Claude model selected: {model_name}")
    else:
        logger.error("No valid Claude model found – سيتم تعطيل تحليل الأخبار")

    md = MarketData(SYMBOLS)
    asyncio.create_task(safe_twelvedata_ws(md))

    sig_gen = SignalGenerator(md)
    # إذا وجدنا نموذج صحيح، نحدث المزاج العام (اختيارياً)
    if model_name:
        await sig_gen.update_sentiment()   # الآن يمكننا تفعيلها لأننا سنستخدم النموذج الصحيح
    else:
        logger.warning("تخطي تحديث المزاج العام لعدم وجود نموذج")

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
                    logger.error(f"Error evaluating {sym}: {e}")
            await asyncio.sleep(30)

    asyncio.create_task(scan_loop())
    asyncio.create_task(tm.monitor_trades())
    asyncio.create_task(run_web_server())

    # تشغيل البوت
    logger.info("Starting bot...")
    await bot.app.initialize()
    await bot.app.start()
    await bot.app.updater.start_polling()
    logger.info("Bot polling started")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
