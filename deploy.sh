#!/bin/bash
 
PROJECT_ID="gwx-internship-01"
REGION="us-east1"
SERVICE_NAME="payu-auth-service"
GAR_REPO="us-east1-docker.pkg.dev/$PROJECT_ID/gwx-gar-intern-01"
IMAGE="$GAR_REPO/payu-auth-service:latest"
 
DB_USER="santhiyas"
DB_PASS="D5#0GFh0LLenU2pqfc7"
DB_NAME="payu"
DB_HOST="34.23.138.181"
DB_PORT=5432
CONN_NAME="gwx-internship-01:us-east1:gwx-csql-intern-01"
DB_URL="postgresql+asyncpg://$DB_USER:$DB_PASS@/$DB_NAME?host=/cloudsql/$CONN_NAME"

echo "Building Backend..."
docker build -t $IMAGE .
docker push $IMAGE
 
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --region=$REGION \
  --allow-unauthenticated \
  --project=$PROJECT_ID \
  --platform=managed \
  --port=8001 \
  --max-instances=2 \
  --min-instances=0 \
  --min=0 \
  --max=2 \
  --service-account gwx-cloudrun-sa-01@gwx-internship-01.iam.gserviceaccount.com \
  --add-cloudsql-instances gwx-internship-01:us-east1:gwx-csql-intern-01 \
  --set-env-vars="DB_URL=$DB_URL,DB_HOST=$DB_HOST,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASS,DB_NAME=$DB_NAME,DB_PORT=$DB_PORT"
  
# echo "Backend is live!"