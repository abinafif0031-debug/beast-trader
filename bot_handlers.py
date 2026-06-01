from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

class TradingBot:
    def __init__(self, token, signal_generator, market_data):
        self.app = Application.builder().token(token).build()
        self.signal_gen = signal_generator
        self.md = market_data

        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.analyze_symbol))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🦁 البوت الوحش جاهز للانقضاض")

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("الإحصائيات غير مفعلة حالياً")

    async def analyze_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = update.message.text.upper().strip()
        await update.message.reply_text(f"طلب تحليل {symbol} قيد التطوير")

    async def send_message(self, chat_id, text):
        await self.app.bot.send_message(chat_id=chat_id, text=text)