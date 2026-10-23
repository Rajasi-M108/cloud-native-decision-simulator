# Build from the platform/ root, not backend/, so paths mirror local dev
# (app/data.py resolves BASE as two levels up from itself, i.e. /app here):
#   docker build -f backend/Dockerfile -t bpi-api .
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app/ ./backend/app/
# Model + processed-data artifacts baked into the image for simplicity;
# swap for S3 reads (boto3) once DATABASE_URL / bucket access is wired up.
COPY ml/artifacts ./ml/artifacts
COPY data/processed ./data/processed

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
