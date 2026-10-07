# 🔧 Railway Deployment Fix

## The Issue
Railway couldn't detect the start command. I've created multiple configuration files to fix this.

## ✅ What I Fixed

### 1. Updated Files:
- ✅ `railway.toml` - Updated with correct builder format
- ✅ `Dockerfile.railway` - Fixed CMD format
- ✅ `Procfile` - Added as backup
- ✅ `nixpacks.toml` - Railway's preferred config

### 2. Push These Changes:
```bash
git add .
git commit -m "Fix Railway deployment configuration"
git push origin main
```

Railway will automatically redeploy once you push.

## 🎯 Alternative: Manual Configuration in Railway

If the auto-deploy still fails, configure manually in Railway:

### In Railway Dashboard:

1. **Go to your service Settings**
2. **Click "Deploy" tab**
3. **Set these values:**

**Builder**: `DOCKERFILE`  
**Dockerfile Path**: `Dockerfile.railway`  
**Start Command**: `uvicorn services.inference_api:app --host 0.0.0.0 --port $PORT`

### Required Environment Variables:
```
PYTHONPATH=/app/src
MLFLOW_TRACKING_URI=https://your-mlflow-service.railway.app
MLFLOW_REGISTERED_MODEL_NAME=forecasting-model
MLFLOW_MODEL_STAGE=Production
REGISTRY_REFRESH_SECONDS=60
```

## 🐛 If Build Still Fails

### Option A: Simpler Dockerfile
If the current Dockerfile fails, try this minimal version:

Create `Dockerfile.simple`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

COPY . .

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "services.inference_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then in Railway Settings → Deploy:
- Dockerfile Path: `Dockerfile.simple`

### Option B: Use Nixpacks (No Dockerfile)
1. **Delete or rename** `Dockerfile.railway` (Railway will ignore it)
2. **Keep** `nixpacks.toml` (already created)
3. **Redeploy** - Railway will use Nixpacks automatically

### Option C: Start from Scratch
1. In Railway, **Delete the current service**
2. **Create new service** → "GitHub Repo"
3. **Let Railway auto-detect** (it should find `nixpacks.toml`)
4. **Add environment variables** as shown above

## 📋 Deployment Checklist

- [ ] Pushed latest code to GitHub
- [ ] Railway has `nixpacks.toml` or `Dockerfile.railway`
- [ ] Start command is configured
- [ ] Environment variables are set:
  - [ ] `PYTHONPATH=/app/src`
  - [ ] `MLFLOW_TRACKING_URI` (your MLflow URL)
  - [ ] `MLFLOW_REGISTERED_MODEL_NAME=forecasting-model`
  - [ ] `MLFLOW_MODEL_STAGE=Production`
- [ ] PostgreSQL service is added and linked
- [ ] MLflow service is running

## 🔍 Debug Build Issues

### View Logs in Railway:
1. Click on your service
2. Go to "Deployments" tab
3. Click the failed deployment
4. Check the build logs

### Common Issues:

**"No Python command found"**
- Solution: nixpacks.toml should handle this

**"Module not found"**
- Check: `PYTHONPATH=/app/src` is set

**"Port binding error"**
- Railway sets `$PORT` automatically - don't hardcode it

**"requirements.txt not found"**
- Make sure it's `requirements.api.txt` in the root

## 🚀 Quick Test After Fix

Once deployed successfully:

```bash
# Health check
curl https://your-service.railway.app/

# Should return:
# {"status": "ok", "model": "forecasting-model", "stage": "Production"}
```

## 💡 Pro Tip: Railway Template

For future deployments, you can create a Railway template:
1. Get deployment working once
2. Click "Share" → "Create Template"
3. One-click deploys next time

## 🆘 Still Having Issues?

Try the **Render.com** deployment instead:
- See `DEPLOYMENT.md` → Option 2: Render.com
- Very similar to Railway but sometimes more forgiving with Docker builds

---

**Next Steps:**
1. Commit these fixes: `git add . && git commit -m "Fix Railway config" && git push`
2. Watch Railway dashboard for new deployment
3. Check logs if it fails
4. Test the endpoints once deployed
