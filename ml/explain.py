"""
Step 4: Explainable AI (SHAP)
Computes SHAP values for the best sales-prediction model and turns the top
features per prediction into a short natural-language explanation — this is
what the "explainability microservice" (Lambda, per the AWS design) wraps.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

BASE = Path(__file__).resolve().parents[1]
ARTIFACTS = BASE / "ml" / "artifacts"
DATA = BASE / "data" / "processed" / "superstore_clean.csv"

NUMERIC_FEATURES = ["Quantity", "Discount", "Profit"]
CATEGORICAL_FEATURES = ["Ship Mode", "Segment", "Region", "Category", "Sub-Category"]


def nl_explanation(row, contributions, base_value, prediction):
    """Turn top SHAP contributors into a manager-facing sentence."""
    top = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
    parts = []
    for feat, val in top:
        direction = "pushed the prediction up" if val > 0 else "pulled the prediction down"
        parts.append(f"{feat} ({direction} by {abs(val):.2f})")
    return f"Predicted sales of {prediction:.2f} vs. an average of {base_value:.2f}, mainly driven by: " + "; ".join(parts) + "."


def main():
    pipe = joblib.load(ARTIFACTS / "best_sales_model.joblib")
    df = pd.read_csv(DATA)
    sample = df.sample(n=min(200, len(df)), random_state=42)
    X = sample[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]
    X_trans = prep.transform(X)
    if hasattr(X_trans, "toarray"):
        X_trans = X_trans.toarray()

    feature_names = prep.get_feature_names_out()

    # TreeExplainer for RF/XGBoost, else fall back to a generic (linear) explainer
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_trans)
        base_value = explainer.expected_value
    except Exception:
        explainer = shap.Explainer(model, X_trans)
        sv = explainer(X_trans)
        shap_values = sv.values
        base_value = sv.base_values[0] if hasattr(sv.base_values, "__len__") else sv.base_values

    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.ravel(base_value)[0])

    # Global feature importance
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    global_importance = sorted(
        zip(feature_names, mean_abs_shap.tolist()), key=lambda kv: kv[1], reverse=True
    )
    with open(ARTIFACTS / "shap_global_importance.json", "w") as f:
        json.dump([{"feature": f_, "mean_abs_shap": round(v, 4)} for f_, v in global_importance[:15]], f, indent=2)

    # Per-record explanations for a handful of sample transactions
    preds = model.predict(X_trans)
    explanations = []
    for i in range(min(15, len(sample))):
        contributions = dict(zip(feature_names, shap_values[i].tolist()))
        text = nl_explanation(sample.iloc[i], contributions, base_value, preds[i])
        explanations.append(
            {
                "index": int(sample.index[i]),
                "prediction": float(preds[i]),
                "explanation": text,
            }
        )

    with open(ARTIFACTS / "sample_explanations.json", "w") as f:
        json.dump(explanations, f, indent=2)

    print("Top global drivers of predicted sales:")
    for f_, v in global_importance[:8]:
        print(f"  {f_}: {v:.3f}")
    print(f"\nSaved SHAP artifacts to {ARTIFACTS}")


if __name__ == "__main__":
    main()
