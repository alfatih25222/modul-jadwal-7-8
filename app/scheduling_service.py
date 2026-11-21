from __future__ import annotations

from typing import Any

from app.conflict_detector import detect_schedule_conflict
from app.observer import ScheduleSubject


class ScheduleValidationError(ValueError):
    """Error validasi saat membuat atau mengubah jadwal."""


class ScheduleNotFoundError(KeyError):
    """Error ketika jadwal dengan ID tertentu tidak ditemukan."""


class SchedulingService:
    """Mengelola CRUD jadwal kuliah, kapasitas ruangan, deteksi bentrok, dan notifikasi."""

    def __init__(
        self,
        room_capacities: dict[str, int] | None = None,
        initial_schedules: list[dict[str, Any]] | None = None,
        subject: ScheduleSubject | None = None,
    ) -> None:
        # Kapasitas ruangan dinormalisasi ke lowercase agar konsisten (misal 'a101': 45)
        self.room_capacities: dict[str, int] = {
            room.strip().lower(): cap for room, cap in (room_capacities or {}).items()
        }
        self.subject = subject
        self._schedules: dict[str, dict[str, Any]] = {}
        for item in initial_schedules or []:
            self.create_schedule(item, notify_observers=False)

    def set_room_capacity(self, ruangan: str, kapasitas: int) -> None:
        if kapasitas <= 0:
            raise ScheduleValidationError("Kapasitas ruangan harus lebih besar dari 0.")
        self.room_capacities[ruangan.strip().lower()] = kapasitas

    def list_schedules(self) -> list[dict[str, Any]]:
        return [dict(s) for s in self._schedules.values()]

    def get_schedule(self, schedule_id: str) -> dict[str, Any]:
        if schedule_id not in self._schedules:
            raise ScheduleNotFoundError(f"Jadwal '{schedule_id}' tidak ditemukan.")
        return dict(self._schedules[schedule_id])

    def _validate_capacity(self, schedule: dict[str, Any]) -> None:
        ruangan = str(schedule["ruangan"]).strip()
        room_key = ruangan.lower()
        enrolled = int(schedule.get("enrolled", 0))

        if enrolled < 0:
            raise ScheduleValidationError("Jumlah mahasiswa enrolled tidak boleh negatif.")

        if room_key in self.room_capacities:
            capacity = self.room_capacities[room_key]
            if enrolled > capacity:
                raise ScheduleValidationError(
                    f"Kapasitas ruangan '{ruangan}' ({capacity}) tidak mencukupi untuk {enrolled} mahasiswa."
                )

    def _validate_no_conflicts(self, candidate_schedules: list[dict[str, Any]]) -> None:
        conflicts = detect_schedule_conflict(candidate_schedules)
        if conflicts:
            types = ", ".join(sorted({c["type"] for c in conflicts}))
            raise ScheduleValidationError(f"Terjadi bentrok jadwal ({types}).")

    def _emit_notification(self, event_type: str, schedule_item: dict[str, Any]) -> None:
        if self.subject is not None:
            payload = {
                "schedule": dict(schedule_item),
                "students": schedule_item.get("students"),
            }
            self.subject.notify(event_type, payload)

    def create_schedule(
        self,
        schedule: dict[str, Any],
        notify_observers: bool = True,
    ) -> dict[str, Any]:
        sched_id = str(schedule.get("id", "")).strip()
        if not sched_id:
            raise ScheduleValidationError("Field 'id' jadwal wajib diisi.")
        if sched_id in self._schedules:
            raise ScheduleValidationError(f"Jadwal dengan id '{sched_id}' sudah ada.")

        new_item = dict(schedule)
        new_item["id"] = sched_id
        new_item["enrolled"] = int(new_item.get("enrolled", 0))

        self._validate_capacity(new_item)
        self._validate_no_conflicts(self.list_schedules() + [new_item])

        self._schedules[sched_id] = new_item
        if notify_observers:
            self._emit_notification("SCHEDULE_CREATED", new_item)
        return dict(new_item)

    def update_schedule(
        self,
        schedule_id: str,
        updates: dict[str, Any],
        notify_observers: bool = True,
    ) -> dict[str, Any]:
        existing = self.get_schedule(schedule_id)
        updated_item = dict(existing)
        updated_item.update(updates)
        updated_item["id"] = schedule_id
        updated_item["enrolled"] = int(updated_item.get("enrolled", 0))

        self._validate_capacity(updated_item)

        others = [dict(s) for sid, s in self._schedules.items() if sid != schedule_id]
        self._validate_no_conflicts(others + [updated_item])

        self._schedules[schedule_id] = updated_item
        if notify_observers:
            self._emit_notification("SCHEDULE_UPDATED", updated_item)
        return dict(updated_item)

    def delete_schedule(
        self,
        schedule_id: str,
        notify_observers: bool = True,
    ) -> dict[str, Any]:
        existing = self.get_schedule(schedule_id)
        del self._schedules[schedule_id]
        if notify_observers:
            self._emit_notification("SCHEDULE_DELETED", existing)
        return existing