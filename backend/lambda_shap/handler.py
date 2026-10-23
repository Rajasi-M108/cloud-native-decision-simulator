"""
SHAP explainability microservice — deployed as its own Lambda, invoked by the
Fargate API (or directly via its own API Gateway route) so explainability
logic can change independently of the core model-serving path.

Loads the model + precomputed SHAP background at cold start, computes SHAP
values for one prediction request, and returns a natural-language explanation.
"""
import json
import os

import joblib
import numpy as np
import shap

MODEL_PATH = os.environ.get("MODEL_PATH", "/opt/ml/best_sales_model.joblib")
_pipe = None


def _load():
    global _pipe
    if _pipe is None:
        _pipe = joblib.load(MODEL_PATH)
    return _pipe


def _explain(record: dict):
    pipe = _load()
    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]

    import pandas as pd
    df = pd.DataFrame([record])
    X = prep.transform(df)
    if hasattr(X, "toarray"):
        X = X.toarray()
    feature_names = prep.get_feature_names_out()

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)[0]
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.ravel(base_value)[0])

    prediction = float(model.predict(X)[0])
    contributions = dict(zip(feature_names, shap_values.tolist()))
    top = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]

    parts = []
    for feat, val in top:
        direction = "pushed the prediction up" if val > 0 else "pulled the prediction down"
        parts.append(f"{feat} {direction} by {abs(val):.2f}")

    text = (
        f"Predicted sales of {prediction:.2f} vs. an average of {base_value:.2f}, "
        f"mainly driven by: " + "; ".join(parts) + "."
    )
    return {"prediction": prediction, "base_value": base_value, "top_features": top, "explanation": text}


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})
        result = _explain(body)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
