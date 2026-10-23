FROM python:3.11 AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir --target /opt/python --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: -r requirements.txt

FROM public.ecr.aws/lambda/python:3.11
COPY --from=builder /opt/python ${LAMBDA_TASK_ROOT}
COPY handler.py ${LAMBDA_TASK_ROOT}
# Model artifact copied in at build time from ml/artifacts/best_sales_model.joblib
COPY best_sales_model.joblib /opt/ml/best_sales_model.joblib

CMD ["handler.lambda_handler"]

