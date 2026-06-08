import boto3
import pandas as pd
import json
import io
from datetime import datetime, timezone

BUCKET = "stock-market-dwh-deekshitha"
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

s3 = boto3.client("s3", region_name="us-east-2")

def read_bronze(ticker):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"bronze/prices/{ticker}/{today}.json"
    response = s3.get_object(Bucket=BUCKET, Key=key)
    raw = json.loads(response["Body"].read().decode("utf-8"))
    df = pd.DataFrame(raw["records"])
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    df["date"] = pd.to_datetime(raw["records"][0].get("Date", pd.RangeIndex(len(df))))
    df["ticker"] = ticker
    df["fetched_at"] = raw["fetched_at"]
    return df

def transform(df):
    # Standardize column names
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]

    # Fix types
    df["date"] = pd.to_datetime(df["date"])

    # Derived columns
    df["daily_return_pct"] = ((df["close"] - df["open"]) / df["open"] * 100).round(4)
    df["price_range"] = (df["high"] - df["low"]).round(4)
    df["is_positive"] = df["daily_return_pct"] > 0

    # Add processing timestamp
    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    # Drop nulls
    df = df.dropna(subset=["open", "close", "high", "low", "volume"])

    return df

def upload_silver(df, ticker):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"silver/prices/{ticker}/{today}.parquet"

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )
    print(f"✅ Uploaded {ticker} → s3://{BUCKET}/{key}")
    print(f"   Shape: {df.shape[0]} rows x {df.shape[1]} columns")

if __name__ == "__main__":
    for ticker in TICKERS:
        print(f"\nProcessing {ticker}...")
        df = read_bronze(ticker)
        df = transform(df)
        upload_silver(df, ticker)
    print("\n🎉 Silver transformation complete!")