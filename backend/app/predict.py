"""
Live what-if prediction and explanation.

Unlike the other /api/explain endpoints (which serve SHAP results that were
precomputed once by ml/explain.py and baked into the container), this module
invokes the SHAP explainer Lambda function live, on demand, with a single
user-submitted record. This is the genuinely elastic, on-demand compute path
in the architecture: a new AWS Lambda invocation happens for every request.
"""
import json
import os

import boto3

LAMBDA_FUNCTION_NAME = os.getenv("SHAP_LAMBDA_NAME", "bpi-platform-shap-explainer")
AWS_REGION = os.getenv("COGNITO_REGION", "ap-south-1")

_lambda_client = boto3.client("lambda", region_name=AWS_REGION)


def predict_and_explain(record: dict) -> dict:
    payload = {"body": json.dumps(record)}
    response = _lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )
    raw = response["Payload"].read()
    outer = json.loads(raw)

    if response.get("FunctionError"):
        raise RuntimeError(f"Lambda error: {outer}")

    if outer.get("statusCode") != 200:
        raise RuntimeError(outer.get("body", "Lambda invocation failed"))

    return json.loads(outer["body"])

