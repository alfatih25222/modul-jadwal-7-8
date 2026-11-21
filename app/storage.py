from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.observer import ScheduleSubject
from app.scheduling_service import SchedulingService


def save_service_state(service: SchedulingService, file_path: str | Path) -> Path:
    """Menyimpan kapasitas ruangan dan daftar jadwal ke file JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "room_capacities": dict(service.room_capacities),
        "schedules": service.list_schedules(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_service_state(
    file_path: str | Path,
    subject: ScheduleSubject | None = None,
) -> SchedulingService:
    """Memuat state kapasitas ruangan dan jadwal dari file JSON ke SchedulingService."""
    path = Path(file_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    room_capacities = {
        str(room): int(cap) for room, cap in (raw.get("room_capacities") or {}).items()
    }
    schedules = list(raw.get("schedules") or [])
    return SchedulingService(
        room_capacities=room_capacities,
        initial_schedules=schedules,
        subject=subject,
    )