# Provider configuration

This project is deliberately **safe by default**. The local demonstration stack works without provider credentials. The API rejects live synchronization until `CLOUDCOST_ALLOW_LIVE_SYNC=true`, even if provider configuration exists.

> Treat cloud billing data and service-principal secrets as sensitive operational data. Keep them in an approved secrets manager or local environment file that is excluded from source control.

## AWS Cost Explorer

AWS Cost Explorer can query daily cost and usage data and requires explicit permission for the caller. AWS recommends using its SDKs because they handle request signing. [1]

Create a dedicated, read-only billing role or principal following your organization’s access-control policy. Use the least permissions required for Cost Explorer reads. The application does not create, resize, tag, terminate, or mutate AWS resources.

```bash
export CLOUDCOST_AWS_COST_EXPLORER_ENABLED=true
export CLOUDCOST_AWS_REGION=us-east-1
export CLOUDCOST_ALLOW_LIVE_SYNC=true
```

Then call `POST /api/v1/sync/aws`. Review the imported record count in `sync_runs` and validate totals against the AWS console before relying on any recommendation.

## Azure Cost Management

Use a service principal with read-only access at the intended subscription or billing scope. The adapter exchanges client credentials for a management-plane token and calls the Cost Management query endpoint from the server. The browser never receives the client secret.

```bash
export CLOUDCOST_AZURE_COST_MANAGEMENT_ENABLED=true
export CLOUDCOST_AZURE_SUBSCRIPTION_ID=<subscription-id>
export CLOUDCOST_AZURE_TENANT_ID=<tenant-id>
export CLOUDCOST_AZURE_CLIENT_ID=<app-id>
export CLOUDCOST_AZURE_CLIENT_SECRET=<secret>
export CLOUDCOST_ALLOW_LIVE_SYNC=true
```

Then call `POST /api/v1/sync/azure`. The code requests daily `ActualCost` grouped by service. For large, recurring workloads, Azure Cost Management exports may be a more suitable ingestion boundary; Microsoft describes exports as a way to create daily or monthly data exports to storage. [2]

## Required verification before live use

| Check | Why it matters |
|---|---|
| Reconcile a selected date range to the provider console. | Confirms currency, scope, timing, tax treatment, and credit treatment match the intended report. |
| Verify the data source is `live`, not `demo`. | Preserves provenance for financial review. |
| Review each rule’s evidence and confidence. | Optimization suggestions are prompts for validation, not automated resource changes. |
| Keep `ALLOW_LIVE_SYNC` off until credentials and access scope are reviewed. | Prevents accidental API calls from a development setup. |

## References

[1] [AWS, *Using the Cost Explorer API*](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html)

[2] [Microsoft, *Create and manage Cost Management exports*](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-improved-exports)
