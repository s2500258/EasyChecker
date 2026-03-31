from fastapi import APIRouter

from ..schemas import EventIn, IngestResponse
from ..services.ingest_service import ingest_event


# Agent-facing ingest endpoint.
router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestResponse)
def create_event(event: EventIn) -> IngestResponse:
    # Validation happens before the service layer runs.
    result = ingest_event(event)
    return IngestResponse(**result)
