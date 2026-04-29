"""Download proxy endpoint."""

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db
from api.exceptions import raise_external_service_error, raise_not_found
from core.database import SpecRepository


router = APIRouter(tags=["download"])


@router.get("/download/{spec_id}/{library}")
async def download_image(spec_id: str, library: str, db: AsyncSession = Depends(require_db)):
    """
    Proxy download for plot images to avoid CORS issues.

    Returns the image as a downloadable file.
    """

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)

    if not spec:
        raise_not_found("Spec", spec_id)

    # Find the implementation for the requested library
    impl = next((i for i in spec.impls if i.library_id == library), None)
    if not impl or not impl.preview_url:
        raise_not_found(f"Implementation for {spec_id}", library)

    # Fetch the image from GCS
    # Explicit timeout — without it a slow GCS response hangs the request
    # indefinitely. Other handlers in this router tree use 10-30s; pick
    # 15s for image downloads.
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(impl.preview_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise_external_service_error("GCS", str(e))

    # Return as downloadable file
    filename = f"{spec_id}-{library}.png"
    return Response(
        content=response.content,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
