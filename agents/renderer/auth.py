"""The caller check of the renderer, copied from `agents/main.py` (which cannot be imported: it loads ADK).

Cloud Run IAM (`--no-allow-unauthenticated`, `roles/run.invoker`) verifies the ID
token before a request reaches the container and forwards it with the signature
replaced (spike S), so the claims are decoded here without verifying a signature.
Outside `ENVIRONMENT=development` the token's `aud` must be in `RENDERER_AUDIENCES`
and its `email` in `RENDERER_ALLOWED_CALLERS`.

**Which header.** A caller may send its token in `X-Serverless-Authorization`
instead of `Authorization`, and when both are present Cloud Run checks only
`X-Serverless-Authorization` and passes `Authorization` through unchecked. So the
check reads `X-Serverless-Authorization` whenever it is present, and
`Authorization` only when it is not; otherwise any invoker could add a forged,
unsigned `Authorization` that names an allowed email.

**Audiences.** Cloud Run accepts a token only when its `aud` is the service URL,
even for a request to a traffic tag's URL, so `RENDERER_AUDIENCES` holds the
service URL (the deploy step adds it) and never a tag URL. A user's ID token
cannot name an audience: `gcloud auth print-identity-token` carries gcloud's
OAuth client id as `aud`, and Application Default Credentials carry theirs. For
the owner's `adk web` against the deployed renderer, that client id joins the
list and the owner's email joins `RENDERER_ALLOWED_CALLERS` (agents/README.md).
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


def checked_token(request: Request) -> str | None:
    """The header Cloud Run IAM verified: `X-Serverless-Authorization` when present, else `Authorization`."""
    serverless = request.headers.get("x-serverless-authorization")
    return serverless if serverless is not None else request.headers.get("authorization")


def check_caller(request: Request, settings: Annotated[RendererSettings, Depends(get_settings)]) -> None:
    """Outside development: an IAM-forwarded ID token whose `aud` and `email` are allowed."""
    if settings.is_development:
        return
    claims = decode_claims(checked_token(request))
    if claims is None:
        raise CallerRefused(401, "unauthenticated")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if not any(isinstance(item, str) and item in settings.audiences for item in audiences):
        raise CallerRefused(403, "forbidden")
    if claims.get("email") not in settings.allowed_callers:
        raise CallerRefused(403, "forbidden")
