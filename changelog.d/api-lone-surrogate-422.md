### Fixed

- **A lone surrogate in a JSON body no longer turns a 422 into a 500.** FastAPI's
  default validation handler echoes the offending `input` into the 422 body, and
  Starlette's `JSONResponse` cannot UTF-8-encode a lone surrogate such as the JSON
  string `"\ud800"`, so any schema-violating body holding one answered 500. A
  `RequestValidationError` handler in `api/exceptions.py` now renders the same
  `{"detail": [...]}` body ASCII-escaped, which can always be encoded. The
  "Standard error format" section of `docs/reference/api.md` now matches what the
  API returns, including the 422 shape.
- **`POST /feedback` answers 422 for text that is not valid UTF-8.** A lone
  surrogate in any field passed the schema, then made the database driver raise on
  encoding, so the request ended as a 500. `FeedbackRequest` now refuses such
  text up front, before the router or the database sees it.
