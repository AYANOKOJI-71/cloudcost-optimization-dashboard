# Validation record

## Browser verification — local demo workspace

The React dashboard was verified against the running FastAPI service through the exposed local development URL. The interface rendered the local-demo label, month-to-date spend, forecast, provider mix, service allocation, seven ranked savings opportunities, and the server-side credential safety notice.

| Check | Result |
|---|---|
| API-backed dashboard data | Passed. The frontend displayed the seeded FastAPI ledger and recommendations. |
| Cost trend and allocation visuals | Passed. The trend chart, service bars, and provider-donut visualization rendered. |
| Safety disclosure | Passed. The UI stated that live AWS and Azure synchronization is disabled until explicit read-only configuration. |
| In-page optimization navigation | Passed. The savings call to action updated the URL hash to `#recommendations`. |
| Responsive verification | Pending mobile viewport check. |
| Workflow interaction verification | Passed. A local-demo recommendation moved from `open` to `in_review` and then `accepted`; the queue filters reflected each state and no cloud-provider mutation was invoked. |

## Automated checks

| Check | Result |
|---|---|
| FastAPI API tests | Passed: 4 tests. |
| FastAPI Ruff static analysis | Passed. |
| React unit tests | Passed: 3 tests. |
| React ESLint and production build | Passed. |
| Docker Compose execution | Not run in this sandbox because no Docker runtime is installed. The manifest is included for local execution with Docker Compose. |
