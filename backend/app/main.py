from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse

from .config import get_settings
from .models import init_db
from .routes.alerts import router as alerts_router
from .routes.events import router as events_router
from .routes.ingest import router as ingest_router


# FastAPI application entry point.
settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"
LOGO_PATH = STATIC_DIR / "logo1.png"
app = FastAPI(title=settings.app_name, debug=settings.debug, docs_url=None)


@app.on_event("startup")
def on_startup() -> None:
    # Make sure tables and missing columns exist before serving requests.
    init_db()


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    # Reuse the shared project logo as the browser and Swagger favicon.
    return FileResponse(LOGO_PATH, media_type="image/png")


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    # Keep Swagger available at the usual URL while using the shared favicon.
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.app_name} - Swagger UI",
        swagger_favicon_url="/favicon.ico",
    )


app.include_router(ingest_router, prefix=settings.api_v1_prefix)
app.include_router(events_router, prefix=settings.api_v1_prefix)
app.include_router(alerts_router, prefix=settings.api_v1_prefix)
