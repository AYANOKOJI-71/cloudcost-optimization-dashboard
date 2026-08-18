# CloudCost IQ — Cloud Cost Monitoring & Optimization Dashboard

**CloudCost IQ** is a portfolio-ready FinOps dashboard that turns daily AWS and Azure cost records into prioritized, reviewable savings opportunities. It combines a **FastAPI** data and optimization service, **React** dashboard, **PostgreSQL** ledger, and provisioned **Prometheus + Grafana** observability stack.

The repository opens in a safe local demonstration mode: it contains a deterministic development ledger that is clearly identified as demonstration data. It does **not** use cloud credentials, contact provider APIs, or claim the sample values represent a real customer’s bill. Live AWS and Azure synchronization must be enabled explicitly through server-side environment variables after least-privilege access is reviewed.

## Why this project is CV-worthy

| Capability | Evidence in this repository |
|---|---|
| Full-stack engineering | React decision dashboard backed by typed FastAPI endpoints and persistent relational storage. |
| Multi-cloud integration design | Separate AWS Cost Explorer and Azure Cost Management adapters with a shared normalized import contract. |
| Business-impact reasoning | A rule engine turns resource signals into transparent monthly savings estimates, evidence, confidence, and workflow state. |
| Production mindset | Docker Compose, health checks, non-root containers, Prometheus metrics, provisioned Grafana, tests, linting, and CI. |
| Security boundaries | Demo by default, live ingestion hard-disabled by default, credential examples without secrets, and server-side provider tokens only. |

## Product preview

The dashboard highlights month-to-date spend, projected monthly run rate, provider exposure, service concentration, and a ranked optimization queue. Each opportunity explains the affected resource, evidence, confidence level, potential monthly savings, and a human review workflow.

## Architecture

```text
Optional AWS Cost Explorer ─┐
Optional Azure Cost API ────┼──> FastAPI + optimization rules ──> PostgreSQL
Local demonstration ledger ─┘                │
                                             ├──> React dashboard
                                             └──> /metrics ──> Prometheus ──> Grafana
```

Read the detailed [architecture](docs/architecture.md) and [provider configuration guide](docs/provider-configuration.md).

## Run locally

### Docker Compose path

```bash
docker compose up --build
```

| Service | URL | Notes |
|---|---|---|
| CloudCost dashboard | `http://localhost:8080` | Main React application. |
| FastAPI health | `http://localhost:8080/health` | Proxied API liveness endpoint. |
| Prometheus | `http://localhost:9090` | Local metrics explorer. |
| Grafana | `http://localhost:3001` | Login: `admin` / `admin_local_only` — change before non-local use. |

Stop and erase local volumes with `docker compose down -v`.

### Development-server path

```bash
# Terminal 1
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
pnpm install
pnpm dev
```

The frontend proxies `/api`, `/health`, and `/metrics` to FastAPI in development.

## Quality checks

```bash
cd backend && pytest && ruff check app tests
cd frontend && pnpm lint && pnpm test && pnpm build
```

The GitHub Actions Quality Gate executes the same API and dashboard checks on push and pull request.

## Live-provider setup

Copy `.env.example` to `.env` and follow [provider configuration](docs/provider-configuration.md). Do not commit the resulting file. AWS states that Cost Explorer requires explicit permission, and Microsoft documents Cost Management’s scoped query and export paths. [1] [2]

## Safety and limitations

The demonstrated rules are decision-support heuristics. They do not perform automatic rightsizing, storage deletion, or any cloud-resource mutation. Validate a recommendation against application demand, resilience requirements, contract commitments, backup policy, and the provider billing console before action.

## References

[1] [AWS, *Using the Cost Explorer API*](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html)

[2] [Microsoft, *Cost Management REST APIs*](https://learn.microsoft.com/en-us/rest/api/cost-management/)
