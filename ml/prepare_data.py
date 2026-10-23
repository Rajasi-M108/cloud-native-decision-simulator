"""
Step 1: Data preparation / cleaning
Mirrors Phase 1's R preprocessing: discover -> dedupe -> types -> outlier check -> save processed CSV.
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "superstore.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "superstore_clean.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)


def main():
    df = pd.read_csv(RAW)
    print(f"Loaded: {df.shape}")

    # Missing values
    n_missing = df.isnull().sum().sum()
    print(f"Missing values: {n_missing}")

    # Duplicates
    n_dupes = df.duplicated().sum()
    print(f"Duplicate rows: {n_dupes}")
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"After dedupe: {df.shape}")

    # Type checks
    numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=numeric_cols)

    # Basic sanity filters (negative sales/quantity would be data errors, not present here but guard anyway)
    df = df[(df["Sales"] > 0) & (df["Quantity"] > 0)]

    # Derived fields useful downstream
    df["Profit_Margin"] = df["Profit"] / df["Sales"]
    df["Unit_Price"] = df["Sales"] / df["Quantity"]

    df.to_csv(OUT, index=False)
    print(f"Saved cleaned dataset: {OUT} -> {df.shape}")


if __name__ == "__main__":
    main()
