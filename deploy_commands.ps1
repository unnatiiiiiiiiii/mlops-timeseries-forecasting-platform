# PowerShell script for deployment fix

Write-Host "🔧 Fixing Railway deployment..." -ForegroundColor Cyan

# Stage all fixes
git add railway.toml
git add Dockerfile.railway
git add Dockerfile.simple
git add Procfile
git add nixpacks.toml
git add RAILWAY_FIX.md
git add deploy_commands.sh
git add deploy_commands.ps1

# Commit
git commit -m "Fix Railway deployment configuration - add Procfile, nixpacks.toml, and updated Dockerfile"

# Push
git push origin main

Write-Host ""
Write-Host "✅ Pushed fixes to GitHub!" -ForegroundColor Green
Write-Host "🚀 Railway should automatically redeploy now." -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Check Railway dashboard for deployment status." -ForegroundColor White
Write-Host "📖 If still failing, see RAILWAY_FIX.md for manual configuration steps." -ForegroundColor White
