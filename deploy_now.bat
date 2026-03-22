@echo off
echo Deploying LoveGuard to Google Cloud Run...
echo Project: instant-ranking-418806

REM Set the project
gcloud config set project instant-ranking-418806

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

REM Build and deploy
echo Building container...
gcloud builds submit --tag gcr.io/instant-ranking-418806/loveguard-app

echo Deploying to Cloud Run...
gcloud run deploy loveguard-app ^
  --image gcr.io/instant-ranking-418806/loveguard-app ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --port 8080 ^
  --memory 2Gi ^
  --cpu 2 ^
  --max-instances 100 ^
  --set-env-vars "APP_ENV=production,OPENAI_API_KEY=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,STRIPE_SECRET_KEY=sk_test_temp_key_for_demo,STRIPE_PUBLISHABLE_KEY=pk_test_temp_key_for_demo"

echo.
echo Deployment complete!
echo Your LoveGuard app should be live at the URL shown above.
pause