import aiohttp
from config import OPTIONWHALES_KEY

async def check_unusual_options(symbol):
    if not OPTIONWHALES_KEY:
        return 0
    url = "https://api.optionwhales.io/v1/flow/popular"
    headers = {"Authorization": f"Bearer {OPTIONWHALES_KEY}"}
    params = {
        "symbol": symbol,
        "min_premium": 50000,
        "min_volume": 50,
        "direction": "call",
        "timeframe": "30m"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    flows = data.get("results", [])
                    total_premium = sum(f.get("premium",0) for f in flows)
                    call_count = len(flows)
                    if call_count >= 2 and total_premium > 200000:
                        return 3
                    elif call_count >= 1 and total_premium > 100000:
                        return 2
                    elif call_count >= 1:
                        return 1
    except:
        pass
    return 0