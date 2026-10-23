# Deploying to AWS

Prereqs (on your machine, not this chat): AWS account, `aws configure` run with
an IAM user that has admin access (fine for a course project), Terraform >=1.5,
Docker, Node 18+, Python 3.11+.

## 0. One-time setup
```bash
aws configure                      # paste your Access Key ID / Secret / region
cd infra
terraform init
```

Set the DB password and alert email (don't hardcode secrets in .tf files):
```bash
export TF_VAR_db_password="ChooseAStrongPassword123!"
export TF_VAR_alert_email="you@example.com"
```

## 1. First apply (creates VPC, S3, RDS, ECR repos, Cognito, empty ECS service)
```bash
terraform apply
```
This will fail to actually *run* healthy containers on the first pass because
the ECR repos are empty — that's expected. Note the outputs (`ecr_api_repository_url`,
`ecr_shap_lambda_repository_url`, `frontend_bucket`, `cognito_user_pool_id`, etc).

## 2. Build & push the API image
Run the ML pipeline first if you haven't (`ml/train_models.py`, `ml/anomaly_detection.py`,
`ml/explain.py`) so `ml/artifacts/` and `data/processed/` exist — the image bakes them in.
```bash
cd ..                              # back to platform/ root — Dockerfile needs that build context
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -f backend/Dockerfile -t bpi-api .
docker tag bpi-api:latest <ecr_api_repository_url>:latest
docker push <ecr_api_repository_url>:latest
```

## 3. Build & push the SHAP Lambda image
```bash
cd lambda_shap
cp ../../ml/artifacts/best_sales_model.joblib .
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -t bpi-shap-lambda .
docker tag bpi-shap-lambda:latest <ecr_shap_lambda_repository_url>:latest
docker push <ecr_shap_lambda_repository_url>:latest
```

## 4. Re-apply so ECS/Lambda pick up the new images
```bash
cd ../../infra
terraform apply
aws ecs update-service --cluster bpi-platform-cluster --service bpi-platform-api-service --force-new-deployment
aws lambda update-function-code --function-name bpi-platform-shap-explainer --image-uri <ecr_shap_lambda_repository_url>:latest
```

## 5. Build & deploy the frontend
```bash
cd ../frontend
echo "VITE_API_URL=http://<api_load_balancer_dns>" > .env.production
npm run build
aws s3 sync dist/ s3://<frontend_bucket>/ --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

Then open the `frontend_url` output — that's the live dashboard.

## Notes / simplifications from the full design doc
- The ALB is public-facing directly (no API Gateway in front of it) to keep
  this deployable without an API Gateway VPC Link — still fronted by CloudFront
  for the static site. Add API Gateway + VPC Link later if you want a single
  domain for both frontend and API.
- SageMaker was simplified to Fargate/Lambda-hosted model serving (the model
  is trained once locally via `ml/train_models.py` and shipped as an artifact)
  rather than a full SageMaker training pipeline — cheaper and simpler for a
  course project scope, same architectural role (ML compute decoupled from API).
- Everything here uses `db.t3.micro` / minimal Fargate CPU — cheap enough for
  free-tier/education credits. Bump `db_instance_class`, `fargate_cpu`,
  `fargate_memory` in `variables.tf` for real load.

## Cost — what's actually free vs. not
Trimmed on purpose for a student budget:
- **No NAT Gateway** (was ~$32+/month, zero free tier) — Fargate tasks sit in
  public subnets with their own public IP instead of a private subnet behind
  NAT. RDS stays private with no internet route at all — it only needs to
  talk to Fargate over the VPC.
- **RDS is single-AZ, no read replica** — Multi-AZ/replica each stand up a
  second full paid instance; `db.t3.micro` single instance fits the 750
  free-tier hours/month for 12 months.
- **Still NOT free, no way around it**: the **ALB** (~$16-20/month baseline,
  no free tier at all) and whatever hours the **Fargate task** actually runs
  (small, roughly $7-9/month if left on 24/7 at the default 256 CPU/512MB).

**Recommended pattern for a course project:** `terraform apply` when you want
to demo/test/screenshot it working, then `terraform destroy` right after.
Run for a few hours across a few sessions and total cost should land under
$5 for the whole project, even outside free tier. Leaving it running
continuously for weeks is what actually costs money — don't do that.

## Tear down (avoid ongoing charges)
```bash
terraform destroy
```
