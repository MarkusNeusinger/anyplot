"""The gallery search's private list of misses: `POST /search/miss` (`api/search_misses.py`)."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from api.search_misses import SearchMissBody, record_miss


# The parts of a validation error that describe the problem; the others (`input`, `ctx`) can carry the body.
_ERROR_KEYS = ("type", "loc", "msg")


class QuietBodyRoute(APIRoute):
    """A route whose `422` says what is wrong with the body without repeating it.

    The API's validation handler (`api/exceptions.py`) answers with the framework's error list, and
    each entry's `input` is the part of the body that failed: for a body that is not an object, the
    whole of it. A body here holds what a visitor typed, so the entries keep their type, location and
    message and lose the rest before that handler sees them.
    """

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def quiet_handler(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as exc:
                errors = [{key: error[key] for key in _ERROR_KEYS if key in error} for error in exc.errors()]
                # `from None`: the original error holds the body, and nothing may carry it further.
                raise RequestValidationError(errors) from None

        return quiet_handler


router = APIRouter(prefix="/search", tags=["search"], route_class=QuietBodyRoute)


@router.post("/miss", status_code=204, response_class=Response)
async def search_miss(payload: SearchMissBody, request: Request) -> Response:
    """Count a gallery search that found nothing in the whole catalogue, for the owner's private list.

    The text travels in the JSON body and nowhere else, and is never logged. The answer is `204` with
    no body whether the text was counted, dropped by a limit or not counted outside production, so a
    caller learns nothing from it. Only a body that is not `{"query": "<text>"}` gets the framework's
    `422`, without the body in it.
    """
    record_miss(request, payload.query)
    return Response(status_code=204)
