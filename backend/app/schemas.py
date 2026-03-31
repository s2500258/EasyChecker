from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# Request model for incoming agent events.
class EventIn(BaseModel):
    ts: str = Field(..., description="Event timestamp in ISO 8601 format")
    host: str = Field(..., min_length=1, max_length=255)
    os_type: Optional[str] = Field(default=None, max_length=50)
    event_type: str = Field(..., min_length=1, max_length=100)
    event_code: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    severity: str = Field(..., min_length=1, max_length=50)
    username: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    source: Optional[str] = Field(default=None, max_length=255)
    raw_data: Optional[dict[str, Any]] = None


# Response model for stored events returned by the API.
class EventOut(EventIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str


# Response model for generated alerts.
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    severity: str
    host: str
    message: str
    created_at: str
    event_count: int


# Combined response returned by the ingest endpoint.
class IngestResponse(BaseModel):
    event: EventOut
    alerts: list[AlertOut]
