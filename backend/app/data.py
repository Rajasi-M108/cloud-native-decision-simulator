"""
Data access layer.

Local/dev: reads the CSV artifacts produced by the ml/ pipeline directly.
Production: same functions can be repointed at RDS by setting DATABASE_URL
and swapping the pd.read_csv calls below for `pd.read_sql`. Kept as plain
functions (not classes) so that swap is a small, contained change.
"""
import json
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed" / "superstore_clean.csv"
ARTIFACTS = BASE / "ml" / "artifacts"

DATABASE_URL = os.getenv("DATABASE_URL")  # set in production (RDS)


@lru_cache
def load_transactions() -> pd.DataFrame:
    path = ARTIFACTS / "transactions_with_anomalies.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.read_csv(PROCESSED)


@lru_cache
def load_model_comparison() -> dict:
    with open(ARTIFACTS / "model_comparison.json") as f:
        return json.load(f)


@lru_cache
def load_anomaly_summary() -> dict:
    with open(ARTIFACTS / "anomaly_summary.json") as f:
        return json.load(f)


@lru_cache
def load_top_anomalies() -> pd.DataFrame:
    return pd.read_csv(ARTIFACTS / "top_anomalies.csv")


@lru_cache
def load_sample_explanations() -> list:
    with open(ARTIFACTS / "sample_explanations.json") as f:
        return json.load(f)


@lru_cache
def load_global_importance() -> list:
    with open(ARTIFACTS / "shap_global_importance.json") as f:
        return json.load(f)


def summary_metrics() -> dict:
    df = load_transactions()
    return {
        "total_sales": round(float(df["Sales"].sum()), 2),
        "total_profit": round(float(df["Profit"].sum()), 2),
        "avg_order_value": round(float(df["Sales"].mean()), 2),
        "total_orders": int(len(df)),
        "avg_discount": round(float(df["Discount"].mean()), 4),
        "overall_margin_pct": round(100 * float(df["Profit"].sum()) / float(df["Sales"].sum()), 2),
    }


def regional_summary() -> list:
    df = load_transactions()
    g = df.groupby("Region").agg(
        total_sales=("Sales", "sum"),
        total_profit=("Profit", "sum"),
        orders=("Sales", "count"),
    ).reset_index()
    return json.loads(g.round(2).to_json(orient="records"))


def category_summary() -> list:
    df = load_transactions()
    g = df.groupby(["Category", "Sub-Category"]).agg(
        total_sales=("Sales", "sum"),
        total_profit=("Profit", "sum"),
        orders=("Sales", "count"),
    ).reset_index()
    return json.loads(g.round(2).to_json(orient="records"))


@lru_cache
def load_benchmark_global() -> dict:
    with open(ARTIFACTS / "benchmark_global_importance.json") as f:
        return json.load(f)


@lru_cache
def load_benchmark_categories() -> list:
    with open(ARTIFACTS / "benchmark_category_insights.json") as f:
        return json.load(f)

