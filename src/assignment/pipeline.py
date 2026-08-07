"""
Assignment 11 — Defense-in-depth pipeline assembly (TODO).

Wire rate limiter + lab guardrails + judge + audit + monitoring.
You may use Google ADK plugins, LangGraph, NeMo, or pure Python.
"""
from __future__ import annotations

from assignment.rate_limiter import RateLimitPlugin
from assignment.audit_log import AuditLogPlugin
from assignment.monitoring import MonitoringAlert


import re
from urllib.parse import urlparse

ALLOWED_EGRESS_HOSTS = frozenset({"api.vinbank.example", "cases.vinbank.example"})


def is_egress_allowed(destination: str, payload: str) -> bool:
    """Enforce a destination allowlist before any data leaves the agent.

    Return ``True`` only for an approved VinBank HTTPS endpoint and ordinary
    banking payload. Return ``False`` for unknown domains and payloads that
    contain a password, API key, database host, phone number or email address.
    Do not let the LLM's prose decide this policy.
    """
    if not destination or not payload:
        return False

    # 1. Parse URL cleanly and validate scheme + exact hostname match
    try:
        parsed = urlparse(destination)
    except Exception:
        return False

    if parsed.scheme != "https":
        return False

    if parsed.hostname not in ALLOWED_EGRESS_HOSTS:
        return False

    # 2. Check payload for secrets and sensitive internal strings
    secret_patterns = [
        r"\badmin123\b",
        r"sk-[a-zA-Z0-9-]{8,}",
        r"db\.vinbank\.internal(?::\d+)?",
        r"(?:password|mật\s*khẩu)\s*[:=]\s*\S+",
    ]
    for pattern in secret_patterns:
        if re.search(pattern, payload, re.IGNORECASE):
            return False

    # 3. Check payload for PII (phone number, email address)
    pii_patterns = [
        r"(?:\+84|84|0)(?:3|5|7|8|9)\d{8}\b|\b0\d{9,10}\b",
        r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}",
    ]
    for pattern in pii_patterns:
        if re.search(pattern, payload, re.IGNORECASE):
            return False

    return True



def build_production_plugins(
    *,
    max_requests: int = 10,
    window_seconds: int = 60,
    use_llm_judge: bool = True,
) -> list:
    """
    TODO 8: Return an ordered list of plugins / layers:

    1. RateLimitPlugin
    2. InputGuardrailPlugin  (from guardrails.input_guardrails)
    3. OutputGuardrailPlugin / LlmJudge  (from guardrails.output_guardrails)
    4. (optional) NeMo wrapper

    Audit/monitoring can be plugins or side observers — document your choice.
    The action gateway calls ``is_egress_allowed`` separately before any sink.
    """
    raise NotImplementedError("Implement build_production_plugins")


def build_observability():
    """TODO: return (AuditLogPlugin(), MonitoringAlert())."""
    raise NotImplementedError("Implement build_observability")


async def run_assignment_suite(pipeline, student_id: str) -> dict:
    """
    TODO: Run Tests 1–4 from assignment11.md and
    return a dict matching schemas/results.schema.json.

    Write:
      outputs/results.json
      outputs/audit_log.json
      outputs/metrics.json
    """
    raise NotImplementedError("Implement run_assignment_suite")
