#!/usr/bin/env python3
"""Generate an ICS file from a Google Sheet."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build


# ====== Configuration ======
SHEET_ID = "1et9j0e0mSHjjGRXswuVB0bSHbOWPPvDOJREjqopxVtA"
SHEET_TAB_NAME = "2026 Games"
OUTPUT_PATH = os.path.join("docs", "calendar.ics")

# Column names (case-insensitive, punctuation-insensitive)
REQUIRED_COLUMNS = {
    "id": "ID",
    "date": "Date",
    "time": "Time",
    "team": "team",
    "going": "Going?",
}
OPTIONAL_COLUMNS = {
    "giveaway": "Giveaway",
    "tix": "#Tix",
}

DURATION_HOURS = 4

# Google Sheets API setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SERVICE_ACCOUNT_ENV = "SHEETS_SERVICE_ACCOUNT_JSON"


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def _parse_going(value: str) -> bool:
    if value is None:
        return False
    normalized = str(value).strip().lower()
    return normalized in {"true", "yes", "y", "1", "checked"}


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    # Date: MM-DD (assume 2026), Time: HH:MM AM/PM
    combined = f"{date_str.strip()} 2026 {time_str.strip()}"
    local_dt = datetime.strptime(combined, "%m-%d %Y %I:%M %p")
    # Treat as America/Los_Angeles; convert to UTC for ICS stability
    # Use fixed UTC conversion by assuming local time in Pacific
    # Python's zoneinfo is not used to keep deps minimal; instead, use local offset.
    # For accurate DST handling, we use zoneinfo when available.
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+

        pacific = ZoneInfo("America/Los_Angeles")
        local_dt = local_dt.replace(tzinfo=pacific)
        return local_dt.astimezone(timezone.utc)
    except Exception:
        # Fallback: assume standard offset -8 hours
        return local_dt.replace(tzinfo=timezone(timedelta(hours=-8))).astimezone(timezone.utc)


@dataclass(frozen=True)
class GameEvent:
    uid: str
    start_utc: datetime
    end_utc: datetime
    summary: str
    description: Optional[str]


def _build_summary(uid: str, team: str, going: bool, tix: str) -> str:
    prefix = "PP" if going else "TV"
    tix = tix.strip()
    if tix:
        prefix = f"{prefix} ({tix})"
    try:
        uid_num = int(uid)
    except ValueError:
        uid_num = 0
    home_away = "vs" if uid_num < 82 else "@"
    return f"{prefix}: {home_away} {team}".strip()


def _fetch_sheet_values() -> List[List[str]]:
    raw_json = os.environ.get(SERVICE_ACCOUNT_ENV)
    if not raw_json:
        raise RuntimeError(f"Missing env var: {SERVICE_ACCOUNT_ENV}")

    creds_info = json.loads(raw_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    range_name = f"{SHEET_TAB_NAME}!A:Z"
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=range_name).execute()
    values = result.get("values", [])
    if not values:
        raise RuntimeError("No data found in sheet")
    return values


def _build_header_map(header_row: List[str]) -> Dict[str, int]:
    header_map: Dict[str, int] = {}
    for idx, raw in enumerate(header_row):
        key = _normalize_header(raw)
        if key:
            header_map[key] = idx
    return header_map


def _get_cell(row: List[str], idx: int) -> str:
    if idx >= len(row):
        return ""
    return row[idx]

def _get_optional_cell(row: List[str], header_map: Dict[str, int], key: str) -> str:
    candidates = [key]
    if key in OPTIONAL_COLUMNS:
        candidates.append(OPTIONAL_COLUMNS[key])
    for candidate in candidates:
        idx = header_map.get(_normalize_header(candidate))
        if idx is not None:
            value = _get_cell(row, idx)
            return str(value).strip()
    return ""


def _iter_events(values: List[List[str]]) -> Iterable[GameEvent]:
    header_map = _build_header_map(values[0])

    for key in REQUIRED_COLUMNS:
        if key not in header_map:
            raise RuntimeError(
                f"Missing required column '{REQUIRED_COLUMNS[key]}' in sheet header"
            )

    for row in values[1:]:
        uid = _get_cell(row, header_map["id"]).strip()
        if not uid:
            continue

        date_str = _get_cell(row, header_map["date"]).strip()
        time_str = _get_cell(row, header_map["time"]).strip()
        team = _get_cell(row, header_map["team"]).strip()
        going_raw = _get_cell(row, header_map["going"]).strip()
        giveaway = _get_optional_cell(row, header_map, "giveaway")
        tix = _get_optional_cell(row, header_map, "tix")

        if not date_str or not time_str or not team:
            raise RuntimeError(f"Row for UID {uid} missing required fields")

        start_utc = _parse_datetime(date_str, time_str)
        end_utc = start_utc + timedelta(hours=DURATION_HOURS)
        going = _parse_going(going_raw)
        summary = _build_summary(uid, team, going, tix)
        description = f"Giveaway: {giveaway}" if giveaway else None

        yield GameEvent(
            uid=uid,
            start_utc=start_utc,
            end_utc=end_utc,
            summary=summary,
            description=description,
        )


def _format_dt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _render_ics(events: Iterable[GameEvent]) -> str:
    lines: List[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//padres-2026-calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for event in events:
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_ics_escape(event.uid)}",
                f"DTSTAMP:{_format_dt_utc(event.start_utc)}",
                f"DTSTART:{_format_dt_utc(event.start_utc)}",
                f"DTEND:{_format_dt_utc(event.end_utc)}",
                f"SUMMARY:{_ics_escape(event.summary)}",
            ]
        )
        if event.description:
            lines.append(f"DESCRIPTION:{_ics_escape(event.description)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _load_existing(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _write_if_changed(path: str, content: str) -> bool:
    existing = _load_existing(path)
    if existing == content:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return True


def main() -> int:
    values = _fetch_sheet_values()
    def _sort_key(event: GameEvent) -> Tuple[int, str]:
        try:
            return int(event.uid), event.uid
        except ValueError:
            return 0, event.uid

    events = sorted(_iter_events(values), key=_sort_key)
    ics_content = _render_ics(events)
    changed = _write_if_changed(OUTPUT_PATH, ics_content)
    print(f"ICS updated: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
