def build_live_evidence(
    *,
    request: dict,
    privacy: dict,
    data_source: str,
    operations: list[dict],
    memory_hits: list[dict],
    decision: dict,
    vehicle_action: dict,
    latency_ms: int,
    recommendations: list[dict] | None = None,
    lifecycle: dict | None = None,
    audit: list[dict] | None = None,
) -> dict:
    evidence = {
        "request": request,
        "privacy": privacy,
        "data_source": data_source,
        "operations": operations,
        "memory_hits": memory_hits,
        "decision": decision,
        "vehicle_action": vehicle_action,
        "latency_ms": latency_ms,
    }
    if recommendations:
        evidence["recommendations"] = recommendations
    if lifecycle:
        evidence["lifecycle"] = lifecycle
    if audit:
        evidence["audit"] = audit
    return evidence
