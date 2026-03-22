# LoveGuard Deployment Guide

Complete step-by-step guide to deploy LoveGuard with 3-layer architecture to Google Cloud Run.

## 🚀 Quick Deployment (2 Hours to Live!)

### Step 1: Get API Keys (15 minutes)

**OpenAI API Key:**
1. Visit https://platform.openai.com/
2. Sign up/login → API Keys → Create new secret key
3. Copy the key (starts with `sk-`)

**Stripe API Keys:**
1. Visit https://dashboard.stripe.com/
2. Sign up/login → Developers → API keys
3. Copy both keys:
   - Publishable key (`pk_test_...`)
   - Secret key (`sk_test_...`)

### Step 2: Configure Environment (5 minutes)

Edit `.env` file in your project:

```env
OPENAI_API_KEY=sk-your-actual-openai-key
STRIPE_SECRET_KEY=sk_test_your-actual-stripe-secret
STRIPE_PUBLISHABLE_KEY=pk_test_your-actual-stripe-publishable
GOOGLE_CLOUD_PROJECT=loveguard-app
APP_ENV=production
```

### Step 3: Google Cloud Setup (20 minutes)

**Install Google Cloud CLI:**
1. Download from https://cloud.google.com/sdk/docs/install
2. Run installer and restart terminal

**Create Project:**
```bash
gcloud auth login
gcloud projects create loveguard-app --name="LoveGuard App"
gcloud config set project loveguard-app
gcloud billing projects link loveguard-app --billing-account=YOUR_BILLING_ID
```

**Enable APIs:**
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 4: Deploy Application (10 minutes)

**Option A: Automated Deployment**
```bash
cd loveguard-app
python execution/cloud_deployer.py production
```

**Option B: Manual Deployment**
```bash
cd loveguard-app

# Build container
gcloud builds submit --tag gcr.io/loveguard-app/loveguard-app

# Deploy to Cloud Run
gcloud run deploy loveguard-app \
  --image gcr.io/loveguard-app/loveguard-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 2Gi \
  --max-instances 100 \
  --set-env-vars "APP_ENV=production,OPENAI_API_KEY=$OPENAI_API_KEY,STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY"
```

### Step 5: Test & Go Live (10 minutes)

1. **Test the app** at the URL provided by deployment
2. **Try analysis** with sample conversation
3. **Test payment flow** (test mode)
4. **Share your live app URL!**

---

## 🏗️ Architecture Benefits

### Self-Healing System
- **AI fails?** → Fallback keyword analysis keeps working
- **Payment issues?** → App continues in free mode  
- **Errors occur?** → System learns and improves automatically

### Reliability Features
- **99%+ uptime** even if external services fail
- **Automatic fallbacks** for all critical functions
- **Error isolation** prevents cascade failures
- **Self-annealing** improves over time

### 3-Layer Structure
```
Layer 1: Directives (What to do)
├── directives/analyze_conversation.md
├── directives/process_payment.md
└── directives/deploy_application.md

Layer 2: Orchestration (Decision making)  
├── app_orchestrator.py
└── app.py (UI layer)

Layer 3: Execution (Doing the work)
├── execution/ai_analyzer.py
├── execution/crisis_detector.py
├── execution/fallback_analyzer.py
├── execution/stripe_processor.py
└── execution/cloud_deployer.py
```

---

## 🔧 Advanced Configuration

### Custom Domain Setup

1. **Purchase domain** (Namecheap, GoDaddy, etc.)
2. **Map domain to Cloud Run:**
   ```bash
   gcloud run domain-mappings create \
     --domain yourdomain.com \
     --service loveguard-app \
     --region us-central1
   ```
3. **Update DNS** with the provided records

### Environment Variables

**Production Settings:**
```env
APP_ENV=production
DEBUG=False
OPENAI_API_KEY=sk-prod-key
STRIPE_SECRET_KEY=sk_live_key  
STRIPE_PUBLISHABLE_KEY=pk_live_key
```

**Development Settings:**
```env
APP_ENV=development
DEBUG=True
OPENAI_API_KEY=sk-test-key
STRIPE_SECRET_KEY=sk_test_key
STRIPE_PUBLISHABLE_KEY=pk_test_key
```

### Monitoring Setup

**Enable Cloud Monitoring:**
```bash
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

**Set up alerts:**
- Error rate > 5%
- Response time > 2 seconds
- Memory usage > 80%

---

## 🛠️ Troubleshooting

### Common Issues

**Build Fails:**
- Check Dockerfile syntax
- Verify requirements.txt dependencies
- Ensure .env file exists

**Deployment Fails:**
- Verify billing is enabled
- Check project permissions
- Ensure APIs are enabled

**App Not Loading:**
- Check environment variables
- Verify port 8080 is configured
- Review Cloud Run logs

**AI Analysis Fails:**
- Verify OpenAI API key is valid
- Check rate limits
- Fallback system should still work

### Getting Help

**View Logs:**
```bash
gcloud run services logs tail loveguard-app --region us-central1
```

**Debug Locally:**
```bash
streamlit run app.py
```

**Test Components:**
```bash
python quick_test.py
```

---

## 📈 Scaling & Growth

### Traffic Scaling
- **Auto-scaling:** 0-100 instances based on demand
- **Cold start optimization:** Min instances for production
- **Regional deployment:** Multiple regions for global users

### Cost Optimization
- **Pay per request** - only charged when used
- **Automatic sleep** when no traffic
- **Resource right-sizing** based on usage patterns

### Feature Expansion
- **New analysis types:** Add directives + execution scripts
- **Additional AI providers:** Swap in/out easily  
- **Payment methods:** Add new processors
- **Integrations:** API endpoints for third parties

---

## 🎯 Success Metrics

**Technical KPIs:**
- ✅ 99%+ uptime
- ✅ <2 second response times  
- ✅ <5% error rate
- ✅ Automatic recovery from failures

**Business KPIs:**
- 💰 Revenue from premium subscriptions
- 📈 User engagement and retention
- 🛡️ Crisis interventions and safety outcomes
- ⭐ User satisfaction ratings

---

## 🚨 Security & Compliance

### Data Protection
- **HTTPS only** - all traffic encrypted
- **No data storage** - conversations not saved
- **API key encryption** - environment variables secured
- **Stripe PCI compliance** - no card data handled

### Privacy Features
- **Anonymous usage** - no user tracking required
- **Temporary processing** - data discarded after analysis
- **Local fallbacks** - work without external calls
- **Audit logs** - security monitoring enabled

---

**🎉 Congratulations! Your LoveGuard app is now live and helping people stay safe in relationships while generating revenue through a robust, self-healing architecture!**