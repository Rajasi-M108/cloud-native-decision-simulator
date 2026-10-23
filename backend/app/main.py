"""
FastAPI backend for the Cloud-Native Explainable Decision Simulator.

Local dev:   uvicorn app.main:app --reload --port 8000
Production:  runs in ECS Fargate behind an Application Load Balancer (see infra/).
"""
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import data
from . import predict as predict_module
from .auth import get_current_user

app = FastAPI(title="Business Performance Intelligence API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the CloudFront domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_PREDICT_FIELDS = [
    "Quantity", "Discount", "Profit",
    "Ship Mode", "Segment", "Region", "Category", "Sub-Category",
]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/summary")
def summary(user: dict = Depends(get_current_user)):
    return data.summary_metrics()


@app.get("/api/regional")
def regional(user: dict = Depends(get_current_user)):
    return data.regional_summary()


@app.get("/api/categories")
def categories(user: dict = Depends(get_current_user)):
    return data.category_summary()


@app.get("/api/models/comparison")
def model_comparison(user: dict = Depends(get_current_user)):
    """MAE / RMSE / MAPE / R2 for Linear Regression, Random Forest, XGBoost."""
    return data.load_model_comparison()


@app.get("/api/anomalies/summary")
def anomalies_summary(user: dict = Depends(get_current_user)):
    return data.load_anomaly_summary()


@app.get("/api/anomalies/top")
def anomalies_top(limit: int = 20, user: dict = Depends(get_current_user)):
    df = data.load_top_anomalies()
    return df.head(limit).to_dict(orient="records")


@app.get("/api/explain/global")
def explain_global(user: dict = Depends(get_current_user)):
    """Global SHAP feature importance for the sales model."""
    return data.load_global_importance()


@app.get("/api/explain/samples")
def explain_samples(user: dict = Depends(get_current_user)):
    """Natural-language SHAP explanations for a set of sample transactions."""
    return data.load_sample_explanations()


@app.post("/api/predict")
def predict(payload: Dict[str, Any], user: dict = Depends(get_current_user)):
    """
    Live what-if prediction: takes a single user-submitted record, invokes
    the SHAP explainer Lambda function on demand, and returns the predicted
    sales value plus a natural-language explanation of why.
    """
    missing = [f for f in REQUIRED_PREDICT_FIELDS if f not in payload]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing}")

    try:
        return predict_module.predict_and_explain(payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Prediction service error: {e}")


@app.get("/api/transactions")
def transactions(
    region: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    df = data.load_transactions()
    if region:
        df = df[df["Region"] == region]
    if category:
        df = df[df["Category"] == category]
    if df.empty:
        return []
    return df.head(limit).to_dict(orient="records")



@app.get("/api/benchmark/global")
def benchmark_global(user: dict = Depends(get_current_user)):
    """
    What separates startups that survived (were acquired) from startups
    that closed, based on a real dataset of 923 Crunchbase-derived companies.
    """
    return data.load_benchmark_global()


@app.get("/api/benchmark/categories")
def benchmark_categories(user: dict = Depends(get_current_user)):
    """
    Per-industry survival rate and funding benchmarks from the same
    real startup outcome dataset.
    """
    return data.load_benchmark_categories()

