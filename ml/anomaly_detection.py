"""
Step 3: Anomaly detection
Flags unusual transactions (outlier sales/profit, irregular discount-profit combos)
using Isolation Forest, unsupervised (no labels needed, matches the brief).
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "superstore_clean.csv"
OUT_DIR = BASE / "ml" / "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = ["Sales", "Quantity", "Discount", "Profit", "Profit_Margin"]


def main():
    df = pd.read_csv(DATA)
    X = df[FEATURES]

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    # contamination=0.03 -> flag roughly the most extreme 3% of transactions
    model = IsolationForest(n_estimators=300, contamination=0.03, random_state=42)
    model.fit(Xs)

    df["anomaly_score"] = -model.score_samples(Xs)  # higher = more anomalous
    df["is_anomaly"] = model.predict(Xs) == -1

    n_flagged = int(df["is_anomaly"].sum())
    print(f"Flagged {n_flagged} anomalous transactions out of {len(df)}")

    df.to_csv(OUT_DIR / "transactions_with_anomalies.csv", index=False)
    joblib.dump({"model": model, "scaler": scaler, "features": FEATURES}, OUT_DIR / "anomaly_model.joblib")

    top_anomalies = df.sort_values("anomaly_score", ascending=False).head(20)
    top_anomalies.to_csv(OUT_DIR / "top_anomalies.csv", index=False)

    with open(OUT_DIR / "anomaly_summary.json", "w") as f:
        json.dump(
            {
                "total_transactions": len(df),
                "flagged": n_flagged,
                "flagged_pct": round(100 * n_flagged / len(df), 2),
            },
            f,
            indent=2,
        )

    print(f"Saved anomaly artifacts to {OUT_DIR}")


if __name__ == "__main__":
    main()
