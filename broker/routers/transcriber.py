import aiofiles

from fastapi import (
    APIRouter,
    UploadFile,
    Request,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from db.session import get_session
from db.job import (
    job_create,
    job_get,
    job_get_all,
    job_update,
    job_get_next,
)
from db.models import JobStatus, JobType, JobStatusEnum, OutputFormatEnum
from typing import Optional
from settings import get_settings
from pathlib import Path

router = APIRouter(tags=["transcriber"])
settings = get_settings()
db_session = get_session()

api_file_upload_dir = settings.API_FILE_UPLOAD_DIR
api_file_storage_dir = settings.API_FILE_STORAGE_DIR


@router.get("/transcriber")
async def transcribe(
    job_id: str = "", status: Optional[JobStatus] = None
) -> JSONResponse:
    """
    Transcribe audio file.
    """

    if job_id:
        res = job_get(db_session, job_id)
    else:
        res = job_get_all(db_session)

    return JSONResponse(content={"result": res})


@router.post("/transcriber")
async def transcribe_file(
    file: UploadFile,
) -> JSONResponse:
    """
    Transcribe audio file.
    """

    # Create a job for the transcription
    job = job_create(
        db_session,
        job_type=JobType.TRANSCRIPTION,
        filename=file.filename,
        output_format=OutputFormatEnum.SRT,
    )

    try:
        file_path = Path(api_file_upload_dir) / file.filename
        async with aiofiles.open(file_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024)
                if not chunk:
                    break
                await out_file.write(chunk)
    except Exception as e:
        job = job_update(db_session, job["uuid"], status=JobStatus.FAILED, error=str(e))
        return JSONResponse(content={"result": {"error": str(e)}}, status_code=500)

    job = job_update(db_session, job["uuid"], status=JobStatusEnum.UPLOADED)

    return JSONResponse(
        content={
            "result": {
                "uuid": job["uuid"],
                "status": job["status"],
                "job_type": job["job_type"],
                "filename": file.filename,
            }
        }
    )


@router.put("/transcriber/{job_id}")
async def update_transcription_status(job_id: str, request: Request) -> JSONResponse:
    """
    Update the status of a transcription job.
    """

    data = await request.json()
    language = data.get("language")
    model = data.get("model")
    status = data.get("status")
    output_format = data.get("output_format")
    error = data.get("error")

    print(f"Job ID: {job_id}")
    print(f"Language: {language}")
    print(f"Model: {model}")
    print(f"Status: {status}")
    print(f"Output Format: {output_format}")

    job = job_update(
        db_session,
        job_id,
        language=language,
        model_type=model,
        status=status,
        output_format=output_format,
        error=error,
    )

    if not job:
        return JSONResponse(
            content={"result": {"error": "Job not found"}}, status_code=404
        )

    return JSONResponse(
        content={
            "result": {
                "uuid": job["uuid"],
                "status": job["status"],
                "job_type": job["job_type"],
                "filename": job["filename"],
            }
        }
    )


@router.get("/transcriber/{job_id}")
async def get_transcription_job(job_id: str) -> JSONResponse:
    """
    Get the status of a transcription job.
    """

    if job_id == "next":
        job = job_get_next(db_session)
        return JSONResponse(content={"result": jsonable_encoder(job)})

    job = job_get(db_session, job_id)

    if not job:
        return JSONResponse(
            content={"result": {"error": "Job not found"}}, status_code=404
        )

    return JSONResponse(content={"result": {"jobs": [jsonable_encoder(job)]}})


@router.get("/transcriber/{job_id}/file")
async def get_transcription_file(job_id: str) -> FileResponse:
    """
    Get the transcription file.
    """
    job = job_get(db_session, job_id)

    if not job:
        return JSONResponse(
            content={"result": {"error": "Job not found"}}, status_code=404
        )

    file_path = Path(api_file_upload_dir) / job["filename"]

    if not file_path.exists():
        return {"result": {"error": "File not found"}}

    return FileResponse(file_path)


@router.put("/transcriber/{job_id}/result")
async def put_transcription_result(job_id: str, file: UploadFile) -> JSONResponse:
    """
    Upload the transcription result.
    """
    if not job_get(db_session, job_id):
        return JSONResponse(
            content={"result": {"error": "Job not found"}}, status_code=404
        )

    try:
        file_path = Path(api_file_storage_dir) / file.filename
        async with aiofiles.open(file_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024)
                if not chunk:
                    break
                await out_file.write(chunk)

        job = job_update(
            db_session,
            job_id,
            status=JobStatusEnum.COMPLETED,
            error=None,
        )

        return JSONResponse(
            content={
                "result": {
                    "uuid": job["uuid"],
                    "status": job["status"],
                    "job_type": job["job_type"],
                    "filename": file.filename,
                }
            }
        )
    except Exception as e:
        return JSONResponse(content={"result": {"error": str(e)}}, status_code=500)


@router.get("/transcriber/{job_id}/result")
async def get_transcription_result(job_id: str) -> FileResponse:
    """
    Get the transcription result.
    """
    job = job_get(db_session, job_id)

    if not job:
        return JSONResponse(
            content={"result": {"error": "Job not found"}}, status_code=404
        )

    match job["output_format"]:
        case OutputFormatEnum.TXT:
            file_path = Path(api_file_storage_dir) / f"{job['uuid']}.txt"
        case OutputFormatEnum.SRT:
            file_path = Path(api_file_storage_dir) / f"{job['uuid']}.srt"
        case OutputFormatEnum.CSV:
            file_path = Path(api_file_storage_dir) / f"{job['uuid']}.csv"
        case _:
            return JSONResponse(
                content={"result": {"error": "Unsupported output format"}},
                status_code=400,
            )

    if not file_path.exists():
        return {"result": {"error": "File not found"}}

    return FileResponse(file_path)
