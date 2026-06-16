import os
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "analytics")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.4.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")


app = FastAPI(
    title="FIT4110 Lab 04 - Analytics Service",
    version=SERVICE_VERSION,
    description=(
        "Dockerized Analytics Service that receives and aggregates events from Camera, IoT, Access, and Core services."
    ),
)


class EventType(str, Enum):
    camera = "camera"
    iot = "iot"
    access = "access"
    core = "core"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class CameraEvent(BaseModel):
    camera_id: str = Field(..., min_length=3, examples=["CAM-A01"])
    event_type: str = Field(..., examples=["motion_detected"])
    timestamp: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])
    metadata: Optional[Dict] = None


class IoTEvent(BaseModel):
    device_id: str = Field(..., min_length=3, examples=["ESP32-LAB-A01"])
    metric: str = Field(..., examples=["temperature"])
    value: float = Field(..., examples=[31.5])
    timestamp: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])


class AccessEvent(BaseModel):
    access_id: str = Field(..., min_length=3, examples=["ACCESS-A01"])
    person_id: str = Field(..., examples=["P001"])
    action: str = Field(..., examples=["entry"])
    timestamp: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])


class CoreEvent(BaseModel):
    service_id: str = Field(..., min_length=3, examples=["CORE-A01"])
    event_name: str = Field(..., examples=["service_startup"])
    timestamp: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])
    details: Optional[Dict] = None


class EventRecord(BaseModel):
    event_id: str
    event_type: EventType
    source_id: str
    timestamp: str
    received_at: str
    metadata: Optional[Dict] = None


class ReportResponse(BaseModel):
    report_id: str
    report_type: str
    period: str
    event_count: int
    generated_at: str


class DashboardMetrics(BaseModel):
    total_events: int
    events_by_type: Dict[str, int]
    last_updated: str


# In-memory storage
EVENTS: List[Dict] = []
REPORTS: List[Dict] = []


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    problem_type: str = "about:blank",
) -> Dict:
    problem = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    return problem


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        problem = build_problem(
            status_code=exc.status_code,
            title="HTTP Error",
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    problem.setdefault("status", exc.status_code)
    problem.setdefault("title", "HTTP Error")
    problem.setdefault("type", "about:blank")
    problem.setdefault("detail", "Request failed")
    problem.setdefault("instance", str(request.url.path))

    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation error",
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> str:
    """Verify Bearer token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token"
        )
    
    return authorization


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_event_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"EVT-{today}-{len(EVENTS) + 1:05d}"


def next_report_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"RPT-{today}-{len(REPORTS) + 1:04d}"


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="OK",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )


# Event Ingestion Endpoints
@app.post(
    "/api/v1/events/camera",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def receive_camera_event(payload: CameraEvent) -> Dict:
    event_id = next_event_id()
    received_at = now_iso()

    item = {
        "event_id": event_id,
        "event_type": "camera",
        "source_id": payload.camera_id,
        "timestamp": payload.timestamp,
        "received_at": received_at,
        "metadata": payload.metadata or {"event_type": payload.event_type},
    }
    EVENTS.append(item)

    return {"event_id": event_id, "status": "accepted"}


@app.post(
    "/api/v1/events/iot",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def receive_iot_event(payload: IoTEvent) -> Dict:
    event_id = next_event_id()
    received_at = now_iso()

    item = {
        "event_id": event_id,
        "event_type": "iot",
        "source_id": payload.device_id,
        "timestamp": payload.timestamp,
        "received_at": received_at,
        "metadata": {
            "metric": payload.metric,
            "value": payload.value,
        },
    }
    EVENTS.append(item)

    return {"event_id": event_id, "status": "accepted"}


@app.post(
    "/api/v1/events/access",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def receive_access_event(payload: AccessEvent) -> Dict:
    event_id = next_event_id()
    received_at = now_iso()

    item = {
        "event_id": event_id,
        "event_type": "access",
        "source_id": payload.access_id,
        "timestamp": payload.timestamp,
        "received_at": received_at,
        "metadata": {
            "person_id": payload.person_id,
            "action": payload.action,
        },
    }
    EVENTS.append(item)

    return {"event_id": event_id, "status": "accepted"}


@app.post(
    "/api/v1/events/core",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def receive_core_event(payload: CoreEvent) -> Dict:
    event_id = next_event_id()
    received_at = now_iso()

    item = {
        "event_id": event_id,
        "event_type": "core",
        "source_id": payload.service_id,
        "timestamp": payload.timestamp,
        "received_at": received_at,
        "metadata": {
            "event_name": payload.event_name,
            "details": payload.details,
        },
    }
    EVENTS.append(item)

    return {"event_id": event_id, "status": "accepted"}


# Query & Reporting Endpoints
@app.get(
    "/api/v1/events",
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
    },
)
def list_events(
    event_type: Optional[str] = Query(None),
    source_id: Optional[str] = Query(None),
    limit: int = Query(default=20, ge=1, le=100),
) -> Dict[str, List[Dict]]:
    items = EVENTS

    if event_type:
        items = [e for e in items if e["event_type"] == event_type]

    if source_id:
        items = [e for e in items if e["source_id"] == source_id]

    return {"items": items[-limit:]}


@app.get(
    "/api/v1/reports/summary",
    response_model=ReportResponse,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
    },
)
def get_summary_report() -> ReportResponse:
    report_id = next_report_id()
    generated_at = now_iso()

    return ReportResponse(
        report_id=report_id,
        report_type="summary",
        period="today",
        event_count=len(EVENTS),
        generated_at=generated_at,
    )


@app.get(
    "/api/v1/dashboard/metrics",
    response_model=DashboardMetrics,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
    },
)
def get_dashboard_metrics() -> DashboardMetrics:
    event_counts = {}
    for event in EVENTS:
        event_type = event["event_type"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    return DashboardMetrics(
        total_events=len(EVENTS),
        events_by_type=event_counts,
        last_updated=now_iso(),
    )
