"""
Step 2: Predictive modeling
Trains Linear Regression, Random Forest, and XGBoost to predict Sales (the
"forecasting" target, since this dataset has no date/time dimension — see README).
Compares them on MAE, RMSE, MAPE, R^2 and saves the best model + a metrics report.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "superstore_clean.csv"
MODELS_DIR = BASE / "ml" / "artifacts"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Sales"
NUMERIC_FEATURES = ["Quantity", "Discount", "Profit"]
CATEGORICAL_FEATURES = ["Ship Mode", "Segment", "Region", "Category", "Sub-Category"]


def build_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def evaluate(y_true, y_pred):
    return {
        "MAE": round(mean_absolute_error(y_true, y_pred), 4),
        "RMSE": round(np.sqrt(mean_squared_error(y_true, y_pred)), 4),
        "MAPE": round(mean_absolute_percentage_error(y_true, y_pred) * 100, 4),  # in %
        "R2": round(r2_score(y_true, y_pred), 4),
    }


def main():
    df = pd.read_csv(DATA)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    candidates = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1),
        "xgboost": XGBRegressor(
            n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.8,
            colsample_bytree=0.8, random_state=42, n_jobs=-1,
        ),
    }

    results = {}
    fitted_pipelines = {}

    for name, model in candidates.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("model", model)])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        metrics = evaluate(y_test, preds)
        results[name] = metrics
        fitted_pipelines[name] = pipe
        print(f"{name}: {metrics}")

    # Pick best by lowest RMSE
    best_name = min(results, key=lambda k: results[k]["RMSE"])
    best_pipe = fitted_pipelines[best_name]
    print(f"\nBest model: {best_name}")

    joblib.dump(best_pipe, MODELS_DIR / "best_sales_model.joblib")
    joblib.dump(fitted_pipelines, MODELS_DIR / "all_sales_models.joblib")

    with open(MODELS_DIR / "model_comparison.json", "w") as f:
        json.dump({"results": results, "best_model": best_name, "target": TARGET}, f, indent=2)

    # Save a holdout prediction set for the dashboard / SHAP step to reuse
    X_test_out = X_test.copy()
    X_test_out["y_true"] = y_test.values
    X_test_out["y_pred_best"] = best_pipe.predict(X_test)
    X_test_out.to_csv(MODELS_DIR / "holdout_predictions.csv", index=False)

    print(f"\nSaved artifacts to {MODELS_DIR}")


if __name__ == "__main__":
    main()
