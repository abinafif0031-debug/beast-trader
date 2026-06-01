import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "trades.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        entry_price REAL,
        exit_price REAL,
        side TEXT,
        pnl REAL,
        confidence INTEGER,
        exit_reason TEXT,
        created_at TEXT,
        closed_at TEXT
    )''')
    conn.commit()
    conn.close()

def record_trade(symbol, entry, exit_p, side, pnl, confidence, exit_reason):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO trades (symbol, entry_price, exit_price, side, pnl, confidence, exit_reason, created_at, closed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (symbol, entry, exit_p, side, pnl, confidence, exit_reason, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def learn_patterns():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM trades WHERE pnl < 0", conn)
        conn.close()
        if len(df) < 5:
            return None
        return "RSI_MAX=72"
    except:
        return None