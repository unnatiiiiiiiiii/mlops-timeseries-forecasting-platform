# ⚡ 5-Minute Railway Deployment

## Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))

## Steps

### 1️⃣ Push to GitHub (if not already done)
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2️⃣ Deploy on Railway

1. **Go to** [railway.app](https://railway.app)
2. **Click** "Start New Project"
3. **Select** "Deploy from GitHub repo"
4. **Choose** this repository
5. Railway will detect the `Dockerfile.railway` and deploy automatically

### 3️⃣ Add PostgreSQL Database

1. **In your Railway project**, click "+ New"
2. **Select** "Database" → "PostgreSQL"
3. Railway auto-links it to your service

### 4️⃣ Add MLflow Service

1. **Click** "+ New" → "Empty Service"
2. **Name it** "mlflow"
3. **Settings** → Variables → Add:
   ```
   PORT=5000
   ```
4. **Settings** → Deploy → Set:
   - Docker Image: `ghcr.io/mlflow/mlflow:v2.19.0`
   - Start Command: `mlflow server --host 0.0.0.0 --port $PORT --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns`
5. **Settings** → Networking → Generate Domain
6. **Copy the MLflow URL** (e.g., `https://mlflow-production-xxxx.railway.app`)

### 5️⃣ Configure API Environment Variables

**In your main API service**, add these variables:

```
PYTHONPATH=/app/src
MLFLOW_TRACKING_URI=https://your-mlflow.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
MLFLOW_REGISTERED_MODEL_NAME=forecasting-model
MLFLOW_MODEL_STAGE=Production
REGISTRY_REFRESH_SECONDS=60
```

**Note**: `${{Postgres.DATABASE_URL}}` is automatically populated by Railway when you add PostgreSQL.

### 6️⃣ Generate Public Domain

1. **Go to** your API service settings
2. **Networking** → "Generate Domain"
3. **Copy your URL**: `https://your-api.railway.app`

### 7️⃣ Test Your Deployment

**Open API docs:**
```
https://your-api.railway.app/docs
```

**Health check:**
```bash
curl https://your-api.railway.app/
```

**Make a prediction:**
```bash
curl -X POST https://your-api.railway.app/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lag_1": 102.4,
    "lag_7": 98.1,
    "rolling_mean_7": 100.9,
    "day_of_week": 1,
    "month": 3
  }'
```

---

## ✅ You're Done!

Your MLOps API is now live at: `https://your-api.railway.app`

### What's Running:
- ✅ FastAPI Inference API
- ✅ PostgreSQL Database
- ✅ MLflow Tracking Server

### Next Steps:
1. Train and register a model to MLflow
2. Set model alias to "Production"
3. API will automatically load and serve it

---

## 💰 Cost Estimate
- **Free tier**: $5 credit/month (good for testing)
- **Light usage**: ~$5-10/month
- **Production**: ~$15-30/month

---

## 🛠️ Troubleshooting

**"Model unavailable" error?**
- Make sure MLflow has a model registered with alias "Production"
- Check MLFLOW_TRACKING_URI is correct

**Database connection issues?**
- Verify PostgreSQL service is running
- Check DATABASE_URL variable is set

**Import errors?**
- Confirm PYTHONPATH=/app/src is set

---

## 📚 Full Deployment Guide
See [DEPLOYMENT.md](./DEPLOYMENT.md) for more deployment options and detailed instructions.
