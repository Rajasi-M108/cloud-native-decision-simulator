
"""
Industry Benchmark and Lessons - offline batch script.

Trains a small classifier on real startup outcome data (Crunchbase-derived,
923 companies, status = acquired/closed) to learn which factors separate
companies that survived from companies that closed. Produces two JSON
files, computed once in advance, the same way the main project anomaly
endpoint is served (precomputed, not live).

Uses the Random Forest built-in feature importance rather than SHAP,
since SHAP needs a compiled C extension that this machine cannot build
(no Microsoft C++ Build Tools installed). The main project prediction
pipeline already demonstrates real SHAP explainability elsewhere.
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

RAW_CSV = "ml/data/startup_data.csv"
OUT_GLOBAL = "ml/artifacts/benchmark_global_importance.json"
OUT_CATEGORY = "ml/artifacts/benchmark_category_insights.json"

TOP_CATEGORIES = [
    "software", "web", "mobile", "enterprise", "advertising",
    "games_video", "semiconductor", "network_hosting", "biotech",
    "hardware", "ecommerce", "cleantech", "security", "analytics",
    "consulting", "public_relations",
]

FEATURES = [
    "funding_total_usd", "funding_rounds", "relationships", "milestones",
    "age_first_funding_year", "age_last_funding_year",
    "has_VC", "has_angel", "has_roundA", "has_roundB", "has_roundC", "has_roundD",
    "avg_participants", "is_top500",
]

def main():
    df = pd.read_csv(RAW_CSV)

    df = df[df["status"].isin(["acquired", "closed"])].copy()
    df["survived"] = (df["status"] == "acquired").astype(int)

    df["category_code"] = df["category_code"].where(df["category_code"].isin(TOP_CATEGORIES), "other")

    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    X = df[FEATURES].copy()
    y = df["survived"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42, class_weight="balanced")
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    print(f"Holdout accuracy: {acc:.4f}   F1: {f1:.4f}   (n_test={len(y_test)})")

    importances = clf.feature_importances_
    global_importance = sorted(
        [{"feature": f, "importance": round(float(v), 4)} for f, v in zip(FEATURES, importances)],
        key=lambda r: -r["importance"],
    )

    with open(OUT_GLOBAL, "w") as f:
        json.dump({"holdout_accuracy": round(acc, 4), "holdout_f1": round(f1, 4), "value": global_importance}, f, indent=2)

    category_insights = []
    for cat in sorted(df["category_code"].unique()):
        sub = df[df["category_code"] == cat]
        if len(sub) < 10:
            continue
        acquired = sub[sub["survived"] == 1]
        closed = sub[sub["survived"] == 0]
        survival_rate = round(100 * len(acquired) / len(sub), 1)

        insight = {
            "category": cat,
            "n_companies": int(len(sub)),
            "survival_rate_pct": survival_rate,
            "median_funding_survived_usd": float(acquired["funding_total_usd"].median()) if len(acquired) else None,
            "median_funding_closed_usd": float(closed["funding_total_usd"].median()) if len(closed) else None,
            "median_funding_rounds_survived": float(acquired["funding_rounds"].median()) if len(acquired) else None,
            "median_funding_rounds_closed": float(closed["funding_rounds"].median()) if len(closed) else None,
            "median_relationships_survived": float(acquired["relationships"].median()) if len(acquired) else None,
            "median_relationships_closed": float(closed["relationships"].median()) if len(closed) else None,
        }
        category_insights.append(insight)

    with open(OUT_CATEGORY, "w") as f:
        json.dump(category_insights, f, indent=2)

    print(f"\nWrote {OUT_GLOBAL}")
    print(f"Wrote {OUT_CATEGORY}")
    print(f"\n{len(category_insights)} categories with >= 10 companies each.")


if __name__ == "__main__":
    main()

