# Billing

Billing is internal-only in this phase. There is no Stripe integration, no
payment processing, no webhooks, and no external billing service.

## Model

Each workspace has one `workspace_subscriptions` row:

- `workspace_id`
- `plan_name`
- `status`
- optional period timestamps for future billing integrations

New workspaces default to the `free` plan.

## Plans

Plans are defined in `app/billing/plans.py`.

| Plan | Intended use |
| --- | --- |
| `free` | Small pilots and local workspaces. |
| `pro` | Larger internal teams and heavier usage. |

Plan limits drive quota enforcement for uploads, document counts, daily queries,
embedding token limits, LLM token limits, and concurrent job limits.

## Internal Plan Changes

Owners and users with `MANAGE_WORKSPACE` permission can change a workspace plan
through the billing API. Members cannot change plans.

Plan changes are audit logged as `billing.plan_changed`.

## No Stripe Yet

Future Stripe integration should update `WorkspaceSubscription` records and keep
the existing quota flow:

```text
workspace -> subscription -> plan definition -> quota policy
```

Stripe should not replace the quota logic. It should become an external source
of subscription status and plan changes.
