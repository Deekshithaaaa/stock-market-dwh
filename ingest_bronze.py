import yfinance as yf
import boto3
import json
from datetime import datetime, timezone

# Stocks we want to track
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
BUCKET = "stock-market-dwh-deekshitha"

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")
    hist = hist.reset_index()  # moves Date from index to a column
    return {
        "ticker": ticker,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "records": json.loads(hist.to_json(orient="records", date_format="iso"))
    }

def upload_to_s3(data, ticker):
    s3 = boto3.client("s3", region_name="us-east-2")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"bronze/prices/{ticker}/{today}.json"
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json"
    )
    print(f"✅ Uploaded {ticker} → s3://{BUCKET}/{key}")

if __name__ == "__main__":
    for ticker in TICKERS:
        print(f"Fetching {ticker}...")
        data = fetch_stock_data(ticker)
        upload_to_s3(data, ticker)
    print("\n🎉 Bronze ingestion complete!")