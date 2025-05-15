from fastapi import (
    APIRouter,
)
from fastapi.responses import FileResponse, JSONResponse
from db.session import get_session
from settings import get_settings
from pathlib import Path

router = APIRouter(tags=["transcriber"])
settings = get_settings()
db_session = get_session()

api_file_upload_dir = settings.API_FILE_UPLOAD_DIR
api_file_storage_dir = settings.API_FILE_STORAGE_DIR


@router.get("/static/{job_id}")
async def get_static_file(job_id: str) -> FileResponse:
    """
    Get the static file.
    """

    file_path = Path(api_file_upload_dir) / job_id

    if not file_path.exists():
        return JSONResponse(
            content={"detail": {"error": "File not found"}},
            status_code=404,
        )

    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=file_path.name,
        headers={
            "Content-Disposition": f"attachment; filename={file_path.name}",
            "X-Accel-Buffering": "no",
        },
    )
