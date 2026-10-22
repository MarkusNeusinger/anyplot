### Fixed

- **API redirects stay on https.** A request to `https://api.anyplot.ai/specs/`
  was redirected to `http://api.anyplot.ai/specs`, because uvicorn ignores
  Cloud Run's `X-Forwarded-Proto` header. The API now takes only the scheme from
  that header, so the trailing-slash redirect keeps https, while the client
  address keeps coming from the trusted headers as before. (#12227)
