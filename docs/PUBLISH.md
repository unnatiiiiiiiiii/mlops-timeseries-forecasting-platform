# 10-Min Safe Publish Guide (GitHub + GitHub Pages)

Use this to publish one shareable link safely.

## 1) Pre-publish safety check
Run from project root:

```bash
# check secrets-like strings in tracked files
rg -n "(SLACK_WEBHOOK|PASSWORD|TOKEN|SECRET|DATABASE_URL=|AKIA|BEGIN PRIVATE KEY)" . --glob "!*.db" --glob "!.venv/**" --glob "!.deps/**" --glob "!.tmp/**"
```

Expected: no real secret values in commit-ready files.

## 2) Ensure screenshots exist
Place final screenshots in:
- `docs/images/airflow-home.png`
- `docs/images/airflow-grid-success.png`
- `docs/images/mlflow-home.png`
- `docs/images/grafana-home.png`
- `docs/images/metrics-endpoint.png`

## 3) Initialize and push repo (if needed)

```bash
git init
git add .
git commit -m "feat: end-to-end mlops forecasting platform with docs showcase"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

If repo already exists:

```bash
git add .
git commit -m "docs: add public GitHub Pages showcase"
git push
```

## 4) Enable GitHub Pages
In GitHub repo:
- Settings -> Pages
- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`
- Save

Your public link will be:
`https://<your-username>.github.io/<your-repo>/`

## 5) Final public validation
Open your Pages link and verify:
- page loads
- architecture section visible
- screenshots visible
- no credentials shown

## 6) Safe share text
Use this in resume/LinkedIn:

"End-to-end MLOps forecasting platform with autonomous drift-triggered retraining, model registry governance, canary rollout controls, and Prometheus/Grafana observability."

