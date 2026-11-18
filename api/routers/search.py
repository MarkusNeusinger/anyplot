"""The gallery search's private list of misses: `POST /search/miss` (`api/search_misses.py`)."""

from fastapi import APIRouter, Request, Response

from api.search_misses import SearchMissBody, json_body_doc, read_json_body, record_miss


router = APIRouter(prefix="/search", tags=["search"])


@router.post("/miss", status_code=204, response_class=Response, openapi_extra=json_body_doc(SearchMissBody))
async def search_miss(request: Request) -> Response:
    """Count a gallery search that found nothing in the whole catalogue, for the owner's private list.

    The text travels in the JSON body and nowhere else, and is never logged. The body is read by hand
    and refused with a fixed `413` above 1 KiB before it is parsed (`read_json_body`). The answer is
    `204` with no body whether the text was counted, dropped by a rule or a limit, or not counted
    outside production, so a caller learns nothing from it. A body that is not JSON, or not
    `{"query": "<text>"}`, gets the framework's `422` without the body in it.
    """
    payload = await read_json_body(request, SearchMissBody)
    record_miss(request, payload.query)
    return Response(status_code=204)
