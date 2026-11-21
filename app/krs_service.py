from dataclasses import dataclass, field
from typing import Any


@dataclass
class KrsRecord:
    krs_id: str
    student_id: str
    schedule_id: str
    status: str = "VALID"  # "VALID" | "INVALIDATED"
    invalidation_reason: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class KrsService:
    """Mengelola pendaftaran KRS mahasiswa dan meng-invalidate KRS saat jadwal berubah."""

    def __init__(self) -> None:
        self._records: dict[str, KrsRecord] = {}

    def enroll_krs(self, krs_id: str, student_id: str, schedule_id: str) -> KrsRecord:
        record = KrsRecord(
            krs_id=krs_id,
            student_id=student_id,
            schedule_id=schedule_id,
            status="VALID",
        )
        record.history.append(
            {
                "action": "ENROLLED",
                "schedule_id": schedule_id,
                "status": "VALID",
            }
        )
        self._records[krs_id] = record
        return record

    def get_krs(self, krs_id: str) -> KrsRecord:
        if krs_id not in self._records:
            raise KeyError(f"KRS '{krs_id}' tidak ditemukan.")
        return self._records[krs_id]

    def list_krs_by_schedule(self, schedule_id: str) -> list[KrsRecord]:
        return [rec for rec in self._records.values() if rec.schedule_id == schedule_id]

    def invalidate_by_schedule_change(
        self,
        schedule_id: str,
        reason: str = "Jadwal kuliah berubah",
    ) -> list[KrsRecord]:
        affected: list[KrsRecord] = []
        for rec in self.list_krs_by_schedule(schedule_id):
            rec.status = "INVALIDATED"
            rec.invalidation_reason = reason
            rec.history.append(
                {
                    "action": "INVALIDATED",
                    "schedule_id": schedule_id,
                    "reason": reason,
                }
            )
            affected.append(rec)
        return affected