"""统一事件格式 + 校验"""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID, uuid4


class Event(BaseModel):
    """统一事件格式 — 所有模块必须遵守"""
    event_id: UUID
    event_type: str
    event_version: int = 1
    event_source: str = "client"
    timestamp: datetime
    tenant_id: str
    campus_id: str | None = None
    user_id: str
    app_id: str
    payload: dict
    trace_id: str | None = None


# --- Payload Schemas ---

class PPTGeneratePayload(BaseModel):
    student_count: int
    template: str
    duration_seconds: int

class AuthLoginPayload(BaseModel):
    device_info: dict
    ip_address: str

class AuthHeartbeatPayload(BaseModel):
    pass

class PPTExportPayload(BaseModel):
    format: str
    file_size: int

class PPTImportPayload(BaseModel):
    student_count: int

class AppStartPayload(BaseModel):
    version: str
    os_info: str

class AppErrorPayload(BaseModel):
    error_type: str
    message: str


EVENT_SCHEMAS = {
    "auth.login": AuthLoginPayload,
    "auth.heartbeat": AuthHeartbeatPayload,
    "ppt.generate": PPTGeneratePayload,
    "ppt.export": PPTExportPayload,
    "ppt.import": PPTImportPayload,
    "app.start": AppStartPayload,
    "app.error": AppErrorPayload,
}


def validate_event(event_type: str, payload: dict) -> dict:
    """所有事件入库前必须经过校验"""
    schema = EVENT_SCHEMAS.get(event_type)
    if schema is None:
        raise ValueError(f"Unknown event type: {event_type}")
    return schema(**payload).model_dump()
