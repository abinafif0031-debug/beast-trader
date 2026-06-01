import aiohttp
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, FINNHUB_API_KEY
import finnhub

async def premarket_sentiment():
    finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
    news = finnhub_client.general_news('general', min_id=0)
    headlines = [n['headline'] for n in news[:10]]
    if not headlines:
        return "RISK-ON", "ALL"
    prompt = f"""حلل العناوين التالية وحدد مزاج السوق اليوم:
{chr(10).join(headlines)}
أجب بسطر واحد: تصنيف (RISK-ON أو RISK-OFF) ثم القطاع الأوفر حظاً (مثل TECH, ENERGY, HEALTH).
مثال: RISK-ON TECH"""
    anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=20,
        messages=[{"role":"user","content":prompt}]
    )
    text = resp.content[0].text.strip()
    parts = text.split()
    mood = parts[0] if parts else "NEUTRAL"
    sector = parts[1] if len(parts)>1 else "ALL"
    return mood, sector