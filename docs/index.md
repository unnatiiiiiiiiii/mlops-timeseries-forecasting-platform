# End-to-End MLOps Time-Series Forecasting

A production-style MLOps platform for time-series forecasting with autonomous retraining, model governance, observability, and safe rollout controls.

## One-Minute Overview
- Automated pipelines with Airflow for ingestion, training, drift checks, and rollout gates.
- MLflow experiment tracking + model registry with promotion lock for concurrency safety.
- Real-time inference APIs with FastAPI (standard and registry-backed endpoints).
- Observability with Prometheus/Grafana and run-level telemetry.
- Kubernetes-ready manifests with canary/stable deployment patterns.

## Architecture
```
Airflow DAGs -> Train Pipeline -> MLflow Tracking -> Model Registry -> FastAPI -> Users
      |                |
      |                -> Telemetry -> Prometheus -> Grafana
      -> Drift Monitor DAG (auto-trigger retrain)
```

## Key Production Features
- Autonomous retraining trigger on drift detection (`drift_monitor_trigger_dag`).
- Run isolation (`data/runs/<run_id>`, `models/<run_id>`).
- Promotion lock metrics:
  - `promotion_lock_wait_seconds`
  - `promotion_lock_acquired_total`
  - `promotion_lock_timeout_total`
- Business KPI metrics:
  - `forecast_accuracy_percent`
  - `model_impact_percent`
- Canary gate decisions: `promote`, `hold`, `rollback`.
- Chaos test script for runtime failure simulation.

## Live Local Endpoints (from demo run)
- Airflow: `http://localhost:8080`
- MLflow: `http://localhost:5000`
- API: `http://localhost:8000/health`
- Registry API: `http://localhost:8001/`
- Metrics: `http://localhost:9100/metrics`
- Prometheus: `http://localhost:9092`
- Grafana: `http://localhost:3002`

## Demo Evidence
Add screenshots in `docs/images/` and keep these names:

- `airflow-home.png`
- `airflow-grid-success.png`
- `mlflow-home.png`
- `grafana-home.png`
- `metrics-endpoint.png`

Example markdown once files exist:

```markdown
![Airflow Home](images/airflow-home.png)
![Retrain DAG Success](images/airflow-grid-success.png)
![MLflow](images/mlflow-home.png)
![Grafana](images/grafana-home.png)
![Prometheus Metrics](images/metrics-endpoint.png)
```

## How To Run (local)
```bash
docker compose -f deploy/docker/docker-compose.yml up -d --build
```

## Security Notes
- No live Airflow/Grafana admin endpoints should be exposed publicly.
- Never commit `.env`, tokens, webhooks, or DB credentials.
- Use Vault/External Secrets in cluster deployments.

## Repository
Update this link after pushing:
- Repo: `https://github.com/<your-username>/<your-repo>`

---

Maintained by Unnati. Built as an end-to-end MLOps portfolio project.
