import boto3
import pandas as pd
import io
import json
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

BUCKET = "stock-market-dwh-deekshitha"
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

s3 = boto3.client("s3", region_name="us-east-2")

def read_gold_daily_prices():
    # List all files and pick the most recent one
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix="gold/daily_prices/")
    files = sorted([obj["Key"] for obj in response["Contents"]], reverse=True)
    latest_key = files[0]
    print(f"Reading: {latest_key}")
    response = s3.get_object(Bucket=BUCKET, Key=latest_key)
    df = pd.read_parquet(io.BytesIO(response["Body"].read()))
    return df

def engineer_features(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Rolling features per ticker
    features = []
    for ticker in TICKERS:
        t = df[df["ticker"] == ticker].copy()
        t["rolling_avg_close"]  = t["close"].rolling(3, min_periods=1).mean()
        t["rolling_avg_volume"] = t["volume"].rolling(3, min_periods=1).mean()
        t["close_deviation"]    = (t["close"] - t["rolling_avg_close"]) / (t["rolling_avg_close"] + 1e-9)
        t["volume_deviation"]   = (t["volume"] - t["rolling_avg_volume"]) / (t["rolling_avg_volume"] + 1e-9)
        features.append(t)

    return pd.concat(features, ignore_index=True)

def detect_anomalies(df):
    feature_cols = ["daily_return_pct", "price_range", "close_deviation", "volume_deviation"]
    results = []

    for ticker in TICKERS:
        t = df[df["ticker"] == ticker].copy()
        X = t[feature_cols].fillna(0)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Isolation Forest — contamination=0.15 means ~15% flagged as anomalies
        model = IsolationForest(contamination=0.15, random_state=42)
        t["anomaly_score"] = model.fit_predict(X_scaled)
        t["is_anomaly"] = t["anomaly_score"] == -1

        results.append(t)

    return pd.concat(results, ignore_index=True)

def upload_anomalies(df):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"gold/anomalies/{today}.parquet"

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )
    print(f"✅ Uploaded anomalies → s3://{BUCKET}/{key}")

def print_report(df):
    print("\n📊 Anomaly Detection Report")
    print("=" * 40)
    anomalies = df[df["is_anomaly"] == True]

    for ticker in TICKERS:
        ticker_anomalies = anomalies[anomalies["ticker"] == ticker]
        total = len(df[df["ticker"] == ticker])
        print(f"\n{ticker}: {len(ticker_anomalies)} anomalous days out of {total}")
        for _, row in ticker_anomalies.iterrows():
            print(f"  📅 {str(row['date'])[:10]} | return: {row['daily_return_pct']:.2f}% | range: ${row['price_range']:.2f}")

if __name__ == "__main__":
    print("Reading Gold layer...")
    df = read_gold_daily_prices()

    print("Engineering features...")
    df = engineer_features(df)

    print("Running Isolation Forest anomaly detection...")
    df = detect_anomalies(df)

    upload_anomalies(df)
    print_report(df)
    print("\n🎉 Anomaly detection complete!")