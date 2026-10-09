# Eval fixture cases

Each directory under `cases/` is one case of the regression harness and a development seed for `adk web` (`AGENT_DEV_FIXTURE=<case-id>`):

| File | Contents |
|---|---|
| `case.json` | `spec_id`, `library`, `locale`, `bindings` (`[{"role", "column"}]`), `expected` (`accepted` or `rejected`) and `tags` |
| `data.csv` | The dataset, small and synthetic; parsed exactly like pasted text |
| `snapshot.json` | Optional: the catalogue snapshot (`spec_id`, `title`, `description`, `data_roles`, `notes`, `code`, `library_version`). Without it the snapshot is built from `plots/<spec_id>/` in this checkout |

Fixture data is invented. Never commit a user's data here: promoted feedback cases live in the private case bucket, and the image build excludes `agents/evals/.cases`.
