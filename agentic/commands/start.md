# Start Development Servers

Start both backend and frontend development servers in the background.

## Instructions

Run both commands so they keep running while you work. Use `run_in_background: true` so they don't block the
conversation.

1. Start the FastAPI backend on port 8000:

   ```bash
   uv run uvicorn api.main:app --reload --port 8000
   ```

2. Start the React frontend on port 3000 (configured in `app/vite.config.ts`):

   ```bash
   cd app && yarn dev
   ```

After starting, verify both responded successfully — for example, `curl -fsS http://localhost:8000/health` for
the API and confirm the Vite dev server printed `Local: http://localhost:3000/`. Report any startup errors to
the user instead of declaring success.

## Notes

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000` (port set in `app/vite.config.ts`; do not assume Vite's default 5173)
- Stop the servers with the matching background-process controls when finished.
