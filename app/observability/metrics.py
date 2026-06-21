from threading import Lock

_COUNTERS = {
    "requests_total": 0,
    "requests_failed_total": 0,
    "uploads_total": 0,
    "queries_total": 0,
}
_LOCK = Lock()


def record_request(status_code: int) -> None:
    with _LOCK:
        _COUNTERS["requests_total"] += 1
        if status_code >= 400:
            _COUNTERS["requests_failed_total"] += 1


def record_upload() -> None:
    with _LOCK:
        _COUNTERS["uploads_total"] += 1


def record_query() -> None:
    with _LOCK:
        _COUNTERS["queries_total"] += 1


def render_prometheus_metrics() -> str:
    with _LOCK:
        counters = dict(_COUNTERS)

    lines = [
        "# HELP rag_platform_requests_total Total HTTP requests handled.",
        "# TYPE rag_platform_requests_total counter",
        f"rag_platform_requests_total {counters['requests_total']}",
        "# HELP rag_platform_requests_failed_total Total HTTP requests with status >= 400.",
        "# TYPE rag_platform_requests_failed_total counter",
        f"rag_platform_requests_failed_total {counters['requests_failed_total']}",
        "# HELP rag_platform_uploads_total Successful document uploads.",
        "# TYPE rag_platform_uploads_total counter",
        f"rag_platform_uploads_total {counters['uploads_total']}",
        "# HELP rag_platform_queries_total Successful workspace queries.",
        "# TYPE rag_platform_queries_total counter",
        f"rag_platform_queries_total {counters['queries_total']}",
        "",
    ]

    return "\n".join(lines)


def reset_metrics() -> None:
    with _LOCK:
        for key in _COUNTERS:
            _COUNTERS[key] = 0
