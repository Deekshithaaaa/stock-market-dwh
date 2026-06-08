import boto3
import pandas as pd
import io
from datetime import datetime, timezone

BUCKET = "stock-market-dwh-deekshitha"
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

s3 = boto3.client("s3", region_name="us-east-2")

def read_silver(ticker):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"silver/prices/{ticker}/{today}.parquet"
    response = s3.get_object(Bucket=BUCKET, Key=key)
    df = pd.read_parquet(io.BytesIO(response["Body"].read()))
    return df

def build_daily_prices(all_df):
    """Gold Table 1: clean combined dataset"""
    df = all_df[["date", "ticker", "open", "close", "high", "low", 
                 "volume", "daily_return_pct", "price_range", "is_positive"]].copy()
    df = df.sort_values(["date", "ticker"]).reset_index(drop=True)
    return df

def build_top_performers(all_df):
    """Gold Table 2: per-ticker performance summary"""
    df = all_df.groupby("ticker").agg(
        avg_daily_return    = ("daily_return_pct", "mean"),
        best_day_return     = ("daily_return_pct", "max"),
        worst_day_return    = ("daily_return_pct", "min"),
        total_volume        = ("volume", "sum"),
        avg_price_range     = ("price_range", "mean"),
        positive_days       = ("is_positive", "sum"),
        total_days          = ("is_positive", "count")
    ).reset_index()
    df["positive_day_pct"] = (df["positive_days"] / df["total_days"] * 100).round(2)
    df = df.sort_values("avg_daily_return", ascending=False).reset_index(drop=True)
    return df

def build_market_overview(all_df):
    """Gold Table 3: date-level market summary"""
    df = all_df.groupby("date").agg(
        avg_return          = ("daily_return_pct", "mean"),
        avg_price_range     = ("price_range", "mean"),
        total_volume        = ("volume", "sum"),
        positive_stocks     = ("is_positive", "sum"),
        total_stocks        = ("is_positive", "count")
    ).reset_index()
    df["market_sentiment"] = df["positive_stocks"].apply(
        lambda x: "bullish" if x >= 3 else "bearish"
    )
    df = df.sort_values("date").reset_index(drop=True)
    return df

def upload_gold(df, table_name):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"gold/{table_name}/{today}.parquet"
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )
    print(f"✅ Uploaded {table_name} → s3://{BUCKET}/{key}")
    print(f"   Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(df.to_string(index=False))
    print()

if __name__ == "__main__":
    print("Reading Silver layer...\n")
    all_dfs = [read_silver(ticker) for ticker in TICKERS]
    all_df = pd.concat(all_dfs, ignore_index=True)
    print(f"Combined dataset: {all_df.shape[0]} rows x {all_df.shape[1]} columns\n")

    print("Building Gold tables...\n")

    daily_prices = build_daily_prices(all_df)
    top_performers = build_top_performers(all_df)
    market_overview = build_market_overview(all_df)

    upload_gold(daily_prices, "daily_prices")
    upload_gold(top_performers, "top_performers")
    upload_gold(market_overview, "market_overview")

    print("🎉 Gold layer complete!")