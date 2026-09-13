from __future__ import annotations

from datetime import datetime, timezone

from mcw_core.api.language.language_manager import tr


def format_playtime(seconds: int) -> str:
    """Format total play time in seconds into a localized human-readable string."""
    seconds = max(0, int(seconds))
    if seconds == 0:
        return tr("workspace.playtime.never")

    minutes = seconds // 60
    if minutes == 0:
        return tr("workspace.playtime.under_minute")

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours == 0:
        return tr("workspace.playtime.minutes", minutes=minutes)
    if remaining_minutes == 0:
        return tr("workspace.playtime.hours_only", hours=hours)
    return tr("workspace.playtime.hours_minutes", hours=hours, minutes=remaining_minutes)


def format_last_played(iso_timestamp: str) -> str:
    """Format an ISO 8601 timestamp of last played date into a friendly localized string."""
    if not iso_timestamp or not iso_timestamp.strip():
        return tr("workspace.last_played.never")

    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return str(iso_timestamp)

    now = datetime.now(dt.tzinfo or timezone.utc)
    delta_days = (now.date() - dt.date()).days

    time_str = dt.strftime("%H:%M")
    if delta_days == 0:
        return tr("workspace.last_played.today", time=time_str)
    if delta_days == 1:
        return tr("workspace.last_played.yesterday", time=time_str)
    if 2 <= delta_days <= 7:
        return tr("workspace.last_played.days_ago", count=delta_days)
    return dt.strftime("%Y-%m-%d")
