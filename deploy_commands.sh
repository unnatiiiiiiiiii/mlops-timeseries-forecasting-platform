#!/bin/bash
# Quick deployment fix commands

echo "🔧 Fixing Railway deployment..."

# Stage all fixes
git add railway.toml
git add Dockerfile.railway
git add Dockerfile.simple
git add Procfile
git add nixpacks.toml
git add RAILWAY_FIX.md
git add deploy_commands.sh

# Commit
git commit -m "Fix Railway deployment configuration - add Procfile, nixpacks.toml, and updated Dockerfile"

# Push
git push origin main

echo "✅ Pushed fixes to GitHub!"
echo "🚀 Railway should automatically redeploy now."
echo ""
echo "📋 Check Railway dashboard for deployment status."
echo "📖 If still failing, see RAILWAY_FIX.md for manual configuration steps."
