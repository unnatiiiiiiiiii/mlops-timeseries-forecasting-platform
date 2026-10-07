# 🚀 Deployment Guide - MLOps Time-Series Forecasting

## Quick Deploy Options

### ⚡ Option 1: Railway.app (Recommended - Fastest)

**Best for**: Full-stack deployment with database, minimal configuration

#### Step-by-Step:

1. **Sign up for Railway**
   - Visit [railway.app](https://railway.app)
   - Sign up with GitHub (free $5 credit/month)

2. **Deploy from GitHub**
   ```bash
   # Push your code to GitHub first
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

3. **Create New Project on Railway**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose this repository
   - Railway will auto-detect the Dockerfile

4. **Add PostgreSQL Database**
   - In your Railway project, click "+ New"
   - Select "Database" → "PostgreSQL"
   - Railway will auto-create and link it

5. **Add MLflow Service**
   - Click "+ New" → "Empty Service"
   - Name it "mlflow"
   - Go to Settings → Deploy
   - Docker Image: `ghcr.io/mlflow/mlflow:v2.19.0`
   - Start Command: `mlflow server --host 0.0.0.0 --port $PORT`
   - Generate Domain (to get public URL)

6. **Configure Environment Variables**
   
   In the main API service, add these variables:
   ```
   PYTHONPATH=/app/src
   MLFLOW_TRACKING_URI=https://your-mlflow-service.railway.app
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   MLFLOW_REGISTERED_MODEL_NAME=forecasting-model
   MLFLOW_MODEL_STAGE=Production
   REGISTRY_REFRESH_SECONDS=60
   PORT=8000
   ```

7. **Deploy!**
   - Railway will automatically deploy
   - Get your API URL from the "Deployments" tab
   - Test: `https://your-api.railway.app/docs`

**Cost**: ~$5-20/month depending on usage

---

### 🔥 Option 2: Render.com (Alternative)

**Best for**: Similar to Railway, generous free tier

#### Step-by-Step:

1. **Sign up for Render**
   - Visit [render.com](https://render.com)
   - Sign up with GitHub (free tier available)

2. **Create PostgreSQL Database**
   - Dashboard → "New +" → "PostgreSQL"
   - Name: `mlops-db`
   - Free tier or paid
   - Copy the Internal Database URL

3. **Deploy MLflow**
   - Dashboard → "New +" → "Web Service"
   - Select "Deploy an existing image from a registry"
   - Image URL: `ghcr.io/mlflow/mlflow:v2.19.0`
   - Start Command: `mlflow server --host 0.0.0.0 --port $PORT`
   - Instance Type: Free or Starter
   - Copy the service URL

4. **Deploy API Service**
   - Dashboard → "New +" → "Web Service"
   - Connect your GitHub repo
   - Name: `mlops-api`
   - Environment: Docker
   - Dockerfile Path: `Dockerfile.railway`
   - Add Environment Variables:
     ```
     PYTHONPATH=/app/src
     MLFLOW_TRACKING_URI=https://your-mlflow.onrender.com
     DATABASE_URL=[paste from step 2]
     MLFLOW_REGISTERED_MODEL_NAME=forecasting-model
     MLFLOW_MODEL_STAGE=Production
     PORT=10000
     ```
   - Deploy!

5. **Access Your API**
   - URL: `https://mlops-api.onrender.com/docs`

**Cost**: Free tier available (spins down after inactivity), or $7/month for always-on

---

### ☁️ Option 3: Fly.io (Lightweight & Fast)

**Best for**: API-only deployment, very fast cold starts

#### Quick Deploy:

1. **Install Fly CLI**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login and Launch**
   ```bash
   fly auth login
   fly launch
   ```

3. **Configure fly.toml** (auto-generated, verify these settings):
   ```toml
   app = "your-mlops-api"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile.railway"

   [env]
     PYTHONPATH = "/app/src"
     MLFLOW_REGISTERED_MODEL_NAME = "forecasting-model"
     MLFLOW_MODEL_STAGE = "Production"

   [[services]]
     internal_port = 8000
     protocol = "tcp"

     [[services.ports]]
       port = 80
       handlers = ["http"]

     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
   ```

4. **Set Secrets**
   ```bash
   fly secrets set MLFLOW_TRACKING_URI=your-mlflow-url
   fly secrets set DATABASE_URL=your-db-url
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

**Cost**: Free tier (3GB RAM), ~$3+/month for production

---

### 🏢 Option 4: AWS/GCP/Azure (Production-Grade)

**Best for**: Enterprise production deployments

#### AWS ECS Deployment:

1. **Build and Push Docker Image**
   ```bash
   # Authenticate to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and tag
   docker build -f Dockerfile.railway -t mlops-api .
   docker tag mlops-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/mlops-api:latest

   # Push
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/mlops-api:latest
   ```

2. **Create RDS PostgreSQL Database**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier mlops-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --master-username admin \
     --master-user-password <your-password> \
     --allocated-storage 20
   ```

3. **Create ECS Cluster & Task Definition**
   - Use AWS Console or Terraform
   - Reference: `k8s/deployment.yaml` for container specs

4. **Deploy with Load Balancer**
   - Create Application Load Balancer
   - Configure target groups
   - Deploy ECS service

**Cost**: ~$20-50+/month minimum

---

## 🧪 Local Testing Before Deploy

```bash
# Test locally with Docker
docker build -f Dockerfile.railway -t mlops-api-test .
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e PYTHONPATH=/app/src \
  mlops-api-test

# Visit http://localhost:8000/docs
```

---

## 📊 Deployment Comparison

| Platform | Setup Time | Free Tier | Best For | Complexity |
|----------|------------|-----------|----------|------------|
| **Railway** | 5 min | $5 credit | Full stack, easiest | ⭐ |
| **Render** | 10 min | Yes (limited) | Full stack | ⭐⭐ |
| **Fly.io** | 15 min | Yes | API only, fast | ⭐⭐ |
| **AWS ECS** | 1-2 hrs | No | Production | ⭐⭐⭐⭐⭐ |
| **Kubernetes** | 2-4 hrs | No | Enterprise | ⭐⭐⭐⭐⭐ |

---

## 🔒 Environment Variables Required

### Minimal (for inference API only):
```
PYTHONPATH=/app/src
MLFLOW_TRACKING_URI=<your-mlflow-url>
MLFLOW_REGISTERED_MODEL_NAME=forecasting-model
MLFLOW_MODEL_STAGE=Production
```

### Full Stack:
```
PYTHONPATH=/app/src
MLFLOW_TRACKING_URI=<mlflow-url>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SLACK_WEBHOOK_URL=<optional-slack-webhook>
MLFLOW_REGISTERED_MODEL_NAME=forecasting-model
MLFLOW_MODEL_STAGE=Production
REGISTRY_REFRESH_SECONDS=60
```

---

## 🧪 Testing Deployment

Once deployed, test your API:

```bash
# Health check
curl https://your-api-url.com/

# Make prediction
curl -X POST https://your-api-url.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lag_1": 102.4,
    "lag_7": 98.1,
    "rolling_mean_7": 100.9,
    "day_of_week": 1,
    "month": 3
  }'
```

Expected response:
```json
{
  "prediction": [103.2]
}
```

---

## 🐛 Troubleshooting

### Issue: "Model unavailable" error
**Solution**: Make sure MLflow is running and accessible, and a model is registered with alias "Production"

### Issue: Port binding errors
**Solution**: Use `$PORT` environment variable (Railway/Render provide this automatically)

### Issue: Import errors
**Solution**: Verify `PYTHONPATH=/app/src` is set

### Issue: Database connection failed
**Solution**: Check DATABASE_URL format and network access

---

## 🎯 Recommended: Railway Deployment

For the fastest and simplest deployment, I recommend **Railway**. It handles:
- ✅ Automatic HTTPS
- ✅ Database provisioning
- ✅ Environment variables
- ✅ Auto-deploys from Git
- ✅ Built-in monitoring
- ✅ Logs and metrics

**Next Steps**: Follow "Option 1: Railway.app" above!

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs)
- [MLflow Deployment Guide](https://mlflow.org/docs/latest/deployment/index.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Need help?** Open an issue or check the troubleshooting section above.
