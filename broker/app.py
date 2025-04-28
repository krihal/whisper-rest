from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from routers.transcriber import router as transcriber_router
from settings import get_settings
from db.job import job_cleanup
from db.session import get_session

settings = get_settings()

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_tags=[
        {
            "name": "transcriber",
            "description": "Transcription operations",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcriber_router, prefix=settings.API_PREFIX, tags=["transcriber"])


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def index():
    """
    Redirect to docs.
    """
    return RedirectResponse(url="/docs")


@app.on_event("startup")
@repeat_every(seconds=60 * 5)  # 5 minutes
def clean_jobs():
    """
    Clean up old jobs stuck in wrong state.
    """
    db_session = get_session()
    job_cleanup(db_session)
