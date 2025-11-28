import os
import time
import requests
import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values

ALPHA_URL = "https://www.alphavantage.co/query"

# --------------------------
# Create Table If Not Exists
# --------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    data_date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, data_date)
);
"""

# --------------------------
# UPSERT (Insert or Update)
# --------------------------
UPSERT_SQL = """
INSERT INTO stock_data (symbol, data_date, open, high, low, close, volume, fetched_at)
VALUES %s
ON CONFLICT (symbol, data_date)
DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    fetched_at = EXCLUDED.fetched_at;
"""

# --------------------------
# Database Connection
# --------------------------
def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
    )

# --------------------------
# Fetch API Data
# --------------------------
def fetch_stock_data(symbol, api_key):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key
    }

    try:
        response = requests.get(ALPHA_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if "Time Series (Daily)" not in data:
            print(f"[ERROR] Unexpected API response for {symbol}: {data}")
            return None

        return data["Time Series (Daily)"]

    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol}: {e}")
        return None

# --------------------------
# Parse JSON
# --------------------------
def parse_data(symbol, raw_json):
    rows = []

    for date_str, values in raw_json.items():
        try:
            rows.append((
                symbol,
                datetime.strptime(date_str, "%Y-%m-%d").date(),
                float(values.get("1. open", 0)),
                float(values.get("2. high", 0)),
                float(values.get("3. low", 0)),
                float(values.get("4. close", 0)),
                int(float(values.get("6. volume", 0))),
                datetime.utcnow()
            ))
        except Exception:
            continue

    return rows

# --------------------------
# Main Function
# --------------------------
def run_fetcher():
    api_key = os.getenv("STOCK_API_KEY")
    symbols = os.getenv("STOCK_SYMBOLS", "AAPL").split(",")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)

    total_rows = 0

    for symbol in symbols:
        symbol = symbol.strip().upper()
        print(f"\n[INFO] Fetching {symbol}...")

        raw_data = fetch_stock_data(symbol, api_key)

        if not raw_data:
            print(f"[WARNING] No data for {symbol}")
            continue

        rows = parse_data(symbol, raw_data)

        if rows:
            execute_values(cursor, UPSERT_SQL, rows)
            total_rows += len(rows)
            print(f"[SUCCESS] {symbol}: {len(rows)} rows inserted/updated")
        else:
            print(f"[WARNING] No valid rows for {symbol}")

        # Prevent Alpha Vantage rate limit issues
        time.sleep(12)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n[INFO] Finished. Total rows processed: {total_rows}")
    return total_rows

# --------------------------
# Run immediately if executed directly
# --------------------------
if __name__ == "__main__":
    run_fetcher()
