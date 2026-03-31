from fastapi import FastAPI

from .config import get_settings
from .models import init_db
from .routes.alerts import router as alerts_router
from .routes.events import router as events_router
from .routes.ingest import router as ingest_router


# FastAPI application entry point.
settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.on_event("startup")
def on_startup() -> None:
    # Make sure tables and missing columns exist before serving requests.
    init_db()


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(ingest_router, prefix=settings.api_v1_prefix)
app.include_router(events_router, prefix=settings.api_v1_prefix)
app.include_router(alerts_router, prefix=settings.api_v1_prefix)
