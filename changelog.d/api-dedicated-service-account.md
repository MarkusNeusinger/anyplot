### Changed

- **anyplot-api runs as its own least-privilege service account**: the API deploys as `anyplot-api@` instead of the Compute Engine default service account, which holds `roles/editor`. The new account gets only Cloud SQL, its six secrets, the agent-cases and static buckets, read access to the telemetry datasets, and the invoker role on `anyplot-agents`, which now admits it as the BFF caller. A unit test keeps the API's deploy account and the agents service's allowed caller equal.
