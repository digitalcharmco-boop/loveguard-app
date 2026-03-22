@echo off
echo Building and deploying LoveGuard to Google Cloud Run...

REM Set your project ID
set PROJECT_ID=loveguard-app

REM Build container image
gcloud builds submit --tag gcr.io/%PROJECT_ID%/loveguard-app

REM Deploy to Cloud Run
gcloud run deploy loveguard-app ^
  --image gcr.io/%PROJECT_ID%/loveguard-app ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --port 8080 ^
  --memory 1Gi ^
  --cpu 1 ^
  --max-instances 10 ^
  --set-env-vars "APP_ENV=production,DEBUG=false" ^
  --set-env-vars "OPENAI_API_KEY=%OPENAI_API_KEY%" ^
  --set-env-vars "STRIPE_SECRET_KEY=%STRIPE_SECRET_KEY%" ^
  --set-env-vars "STRIPE_PUBLISHABLE_KEY=%STRIPE_PUBLISHABLE_KEY%"

echo Deployment complete!