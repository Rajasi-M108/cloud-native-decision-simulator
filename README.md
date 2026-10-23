# AI-Powered Business Performance Intelligence Platform

Team: Shreejita Saha (24BDS1056), Rajasi Mukherjee (24BDS1090)
Dataset: Kaggle "Sample Superstore Dataset"

## Layout
- `ml/` — data prep, forecasting (Linear Regression / Random Forest / XGBoost), anomaly detection, SHAP explainability, model comparison (MAE/RMSE/MAPE/R²)
- `backend/` — FastAPI REST API (serves dashboard data, predictions, explanations)
- `frontend/` — React dashboard (sales, profit, forecasts, anomalies, explanations)
- `infra/` — Terraform for AWS (S3, RDS, ECS Fargate, Cognito, Lambda, CloudWatch)
- `data/` — raw/processed dataset (gitignored; put the Kaggle CSV in `data/raw/`)

## Status
- [ ] Dataset loaded (`data/raw/superstore.csv`)
- [ ] ML pipeline (prep → EDA carried over from Phase 1 → models → SHAP)
- [ ] Backend API
- [ ] Frontend dashboard
- [ ] Terraform infra written
- [ ] AWS account + credentials available
- [ ] Deployed to AWS
