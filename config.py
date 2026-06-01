import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")
OPTIONWHALES_KEY = os.getenv("OPTIONWHALES_KEY")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# قائمة الأسهم – ابدأ بـ 10 أسهم فقط للتجربة، ثم وسّع بعد ما تتأكد إن كل شيء شغال
SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN",
    "META", "GOOGL", "AMD", "SPY", "QQQ"
]