"""ACE-Step API health check utilities."""

import os

import requests

API_URL = os.getenv("ACESTEP_API_URL", "http://127.0.0.1:7860").strip()


def check_health() -> bool:
    """Return True if the ACE-Step API /health endpoint responds 200."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def health_badge_html() -> str:
    """Return an HTML snippet with a coloured badge indicating server status."""
    is_up = check_health()
    if is_up:
        color = "#22c55e"
        label = "API: Online"
    else:
        color = "#ef4444"
        label = "API: Offline"
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;">'
        f'<span style="width:12px;height:12px;border-radius:50%;'
        f"background:{color};display:inline-block;\"></span>"
        f'<span style="font-size:0.9em;">{label}</span>'
        f"</span>"
    )
