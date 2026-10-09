"""The caller check of the renderer, copied from `agents/main.py` (which cannot be imported: it loads ADK).

Cloud Run IAM (`--no-allow-unauthenticated`, `roles/run.invoker`) verifies the ID
token before a request reaches the container and forwards the `Authorization`
header with the signature replaced (spike S), so the claims are decoded here
without verifying a signature. Outside `ENVIRONMENT=development` the token's `aud`
must be in `RENDERER_AUDIENCES` and its `email` in `RENDERER_ALLOWED_CALLERS`.

`RENDERER_AUDIENCES` holds the service URL and the candidate-tag URL, which is the
`aud` of a service account's token (the agents service on Cloud Run). A user's ID
token cannot name an audience: `gcloud auth print-identity-token` carries gcloud's
OAuth client id as `aud`, and Application Default Credentials carry theirs. For the
owner's `adk web` against the deployed renderer, that client id joins the list
and the owner's email joins `RENDERER_ALLOWED_CALLERS` (agents/README.md).
"""

import base64
import binascii
import json
from typing import Annotated, Any

from fastapi import Depends, Request

from .settings import RendererSettings, get_settings


class CallerRefused(Exception):
    """The request carries no acceptable ID token; answered as `{"detail": code}`."""

    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


def decode_claims(authorization: str | None) -> dict[str, Any] | None:
    """The claims of a bearer JWT, decoded without verifying the signature (Cloud Run IAM did)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    parts = authorization[7:].strip().split(".")
    if len(parts) != 3:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, binascii.Error):
        return None
    return claims if isinstance(claims, dict) else None


def check_caller(request: Request, settings: Annotated[RendererSettings, Depends(get_settings)]) -> None:
    """Outside development: an IAM-forwarded ID token whose `aud` and `email` are allowed."""
    if settings.is_development:
        return
    claims = decode_claims(request.headers.get("authorization"))
    if claims is None:
        raise CallerRefused(401, "unauthenticated")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if not any(isinstance(item, str) and item in settings.audiences for item in audiences):
        raise CallerRefused(403, "forbidden")
    if claims.get("email") not in settings.allowed_callers:
        raise CallerRefused(403, "forbidden")
