# Project Management Map

`docs/project-management-map.html` is a standalone, interactive project map for
`rag-platform`. It scans backend, frontend, tests, evals, scripts, docs, infra,
and migrations, then renders a browser-readable dashboard for onboarding,
project management, feature planning, and refactor planning.

Generate it with:

```powershell
python scripts/generate_project_map.py
```

Output:

```txt
docs/project-management-map.html
```

The report includes:

- Executive summary and quick stats.
- System architecture overview.
- FastAPI route inventory.
- Backend function, method, and class inventory.
- Database model and enum inventory.
- Ingestion pipeline map.
- Frontend routes and components.
- Frontend API client functions and helpers.
- Feature management map.
- Test coverage and eval maps.
- Script, docs, deployment, and migration inventory.
- Refactor opportunity dashboard.
- Module dependency tables.
- Management roadmap view.

Use the global search, category filter, collapsible sections, and copy buttons to
inspect specific files, features, risks, and refactor candidates.
