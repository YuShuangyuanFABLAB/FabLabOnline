from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response


REQUEST_COUNT = Counter(
    "fablab_api_requests_total",
    "Total API requests",
    ["method", "path", "status"],
)

REQUEST_DURATION = Histogram(
    "fablab_api_request_duration_seconds",
    "API request duration",
    ["method", "path"],
)

# Gauge 可增可减，反映实时活跃会话数
ACTIVE_SESSIONS = Gauge(
    "fablab_api_active_sessions",
    "Active user sessions",
    ["tenant_id"],
)

EVENTS_RECEIVED = Counter(
    "fablab_events_received_total",
    "Events received",
    ["event_type"],
)


def metrics_endpoint() -> Response:
    return Response(content=generate_latest(), media_type="text/plain")
