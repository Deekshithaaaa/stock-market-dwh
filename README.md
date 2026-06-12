# Stock Market Analytics Data Warehouse on AWS

An end-to-end cloud-native data pipeline that ingests real stock market data daily, transforms it through a medallion architecture on AWS S3, queries it with Amazon Athena, orchestrates it with Apache Airflow, and detects anomalies using machine learning.

## Architecture
Yahoo Finance API
↓
ingest_bronze.py → S3 Bronze (raw JSON, partitioned by ticker/date)
↓
transform_silver.py → S3 Silver (clean Parquet, derived columns)
↓
transform_gold.py → S3 Gold (3 analytical tables, pre-aggregated)
↓
Amazon Athena → SQL analytical queries
↓
detect_anomalies.py → ML anomaly detection (Isolation Forest)
↑
Apache Airflow → Orchestrates full pipeline daily

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Cloud storage | AWS S3 |
| Query engine | Amazon Athena |
| Orchestration | Apache Airflow 3.2.2 |
| ML | scikit-learn (Isolation Forest) |
| Data format | Parquet (columnar) |
| Language | Python 3.12 |
| Libraries | pandas, boto3, yfinance, pyarrow |

## Data Pipeline

### Bronze Layer
- Raw JSON ingested directly from Yahoo Finance API
- 5 tickers: AAPL, GOOGL, MSFT, AMZN, TSLA
- Partitioned by ticker and date: `bronze/prices/AAPL/2026-06-08.json`
- Never modified — source of truth

### Silver Layer
- Cleaned and typed Parquet files
- Derived columns: `daily_return_pct`, `price_range`, `is_positive`
- Nulls removed, schema validated
- Stored at: `silver/prices/AAPL/2026-06-08.parquet`

### Gold Layer
Three analytical tables:
- `daily_prices` — full clean dataset for dashboards
- `top_performers` — per-ticker performance summary (avg return, best/worst day, volume)
- `market_overview` — daily market sentiment (bullish/bearish)

## ML Anomaly Detection

Uses **Isolation Forest** (unsupervised) to flag unusual trading days:
- Features: daily return %, price range, rolling deviation from mean, volume deviation
- Contamination rate: 15% (flags top 15% most unusual days)
- Results saved to `gold/anomalies/` in S3

Sample output:
TSLA: 3 anomalous days
📅 2026-05-11 | return: +5.41% | range: $32.36
📅 2026-05-11 | return: -7.02% | range: $36.09
GOOGL: 3 anomalous days
📅 2026-05-11 | return: +4.41% | range: $18.69

## Airflow DAG

The full pipeline runs daily via a 3-task DAG:
ingest_bronze → transform_silver → transform_gold

## Analytical SQL Queries (Athena)

```sql
-- Top performing stocks by average daily return
SELECT ticker, avg_daily_return, best_day_return, positive_day_pct
FROM stock_market_dwh.top_performers
ORDER BY avg_daily_return DESC;

-- Market sentiment by day
SELECT trading_date, positive_stocks, market_sentiment
FROM stock_market_dwh.market_overview
ORDER BY trading_date DESC;
```

## Setup

### Prerequisites
- AWS account with S3 and Athena access
- Python 3.12+
- Apache Airflow 3.2.2

### Installation
```bash
git clone https://github.com/Deekshithaaaa/stock-market-dwh.git
cd stock-market-dwh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### AWS Configuration
```bash
aws configure
# Enter your AWS Access Key ID, Secret, region (us-east-2), format (json)
```

### Run the pipeline
```bash
# Individual scripts
python ingest_bronze.py
python transform_silver.py
python transform_gold.py
python detect_anomalies.py

# Or via Airflow (runs daily automatically)
airflow standalone
```

## Project Structure
stock-market-dwh/
├── ingest_bronze.py          # Fetch stock data → S3 Bronze
├── transform_silver.py       # Clean JSON → Parquet Silver
├── transform_gold.py         # Build analytical Gold tables
├── detect_anomalies.py       # ML anomaly detection
├── dags/
│   └── stock_market_pipeline.py  # Airflow DAG
├── queries/
│   └── analytical_queries.sql    # Athena SQL queries
├── requirements.txt
└── README.md

## Key Results

- **GOOGL** top performer: +0.22% avg daily return, positive 60% of days
- **TSLA** most volatile: best day +5.41%, worst day -7.02%
- **AAPL & TSLA** most actively traded by volume
- Market overall **bullish** during the tracked period