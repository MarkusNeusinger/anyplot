# Code Style and Conventions

## Python (API, Core, Tests)
- **Linter/Formatter**: Ruff (line-length=120, target=py314)
- **Rules**: E, F, W, I, C, B (ignores E501, C901, B008)
- **Excludes**: plots/, scripts/, .git, .venv, __pycache__, dist, temp
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for public functions
- **Import Order**: stdlib → third-party → local (enforced by ruff I)
- **Async**: SQLAlchemy async, pytest-asyncio (auto mode)

## TypeScript (Frontend)
- **Linter**: ESLint 10 with typescript-eslint
- **Strict mode**: Enabled in tsconfig
- **Target**: ES2020, bundler module resolution
- **Path alias**: `@/` → `./src/`
- **Components**: PascalCase files (e.g., `PlotCard.tsx`), function components only
- **Hooks**: camelCase with `use` prefix (e.g., `useSpecs.ts`)
- **Utils/Types**: camelCase files (e.g., `api.ts`)
- **Exports**: Named exports (no default exports)
- **Styling**: MUI `sx` prop + theme tokens from `app/src/theme/index.ts`. No hardcoded hex colors — use `colors.*`, `semanticColors.*`, `fontSize.*`, `typography.fontFamily` imports. See Serena memory `style_guide` for full token reference.
- **State**: Local state + custom hooks (no Redux/Zustand). Avoid `setState` inside `useEffect` for prop resets — use render-time ref pattern instead.
- **API calls**: Plain `fetch()` in `utils/api.ts`

## Agentic Layer Conventions
- **Script headers**: uv inline script metadata (dependencies declared in-file)
- **CLI**: Click for all workflow scripts
- **Console output**: Rich library, stderr for UI, stdout for state JSON
- **State**: `WorkflowState` persisted at `agentic/runs/{run_id}/state.json`
- **Templates**: `agentic/commands/*.md` with `$1`, `$2`, `$ARGUMENTS` placeholders
- **Execution**: `prompt_claude_code_with_retry()` in `agent.py`
- **Data types**: `TestResult`, `ReviewResult`, `ReviewIssue` in `agent.py`
- **JSON parsing**: `parse_json()` handles markdown-fenced JSON from LLM output

## Plot Implementation Style (KISS)
```python
"""
spec-id: Plot Title
Library: library-name
"""
import matplotlib.pyplot as plt
import numpy as np

# Data
np.random.seed(42)
x = np.random.randn(100)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.scatter(x, y)
ax.set_title('Title')
plt.tight_layout()
plt.savefig('plot.png', dpi=300, bbox_inches='tight')
```
- No functions, no classes, no `if __name__`
- No type hints or docstrings in plot code
- Flow: imports → data → plot → save

## Naming Conventions
- **Spec IDs**: `{plot-type}-{variant}-{modifier}` (lowercase, hyphens)
- **Implementation files**: `{library}.py`
- **Metadata files**: `{library}.yaml`
- **Test naming**: `test_{what_it_does}`
- **All output**: English only (comments, commits, docs, PRs)
