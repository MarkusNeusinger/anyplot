# The project runs on Google Cloud

- Date: 2025-12-07
- Proposed: the API needed its PostgreSQL database once deployed on Cloud Run.
- Decided: Cloud Run for the services, Cloud SQL for PostgreSQL, Cloud Storage for the plot images,
  and Cloud Build for deploys. He confirmed it as his decision on 2026-11-19.
- Where: #529, `CHANGELOG.md`, `README.md`
