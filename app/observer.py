from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class ScheduleObserver(ABC):
    """Interface dasar untuk seluruh stakeholder yang mengamati perubahan jadwal."""

    @abstractmethod
    def update(self, event: dict[str, Any]) -> dict[str, Any]:
        """Menangani event perubahan jadwal dan mengembalikan catatan log notifikasi."""


class StudentObserver(ScheduleObserver):
    """Observer untuk mahasiswa terdampak perubahan jadwal."""

    def __init__(self, channel: str = "email") -> None:
        self.channel = channel
        self.logs: list[dict[str, Any]] = []

    def update(self, event: dict[str, Any]) -> dict[str, Any]:
        schedule = event.get("schedule", {})
        recipients = event.get("students") or schedule.get("students") or ["mahasiswa_terdaftar"]
        message = (
            f"[{self.channel.upper()} -> Mahasiswa {recipients}] "
            f"Event '{event.get('event_type')}' pada jadwal '{schedule.get('matkul', schedule.get('id'))}' "
            f"({schedule.get('hari')}, {schedule.get('jam_mulai')}-{schedule.get('jam_selesai')}, "
            f"Ruang {schedule.get('ruangan')})."
        )
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "role": "student",
            "channel": self.channel,
            "recipients": recipients,
            "event_type": event.get("event_type"),
            "message": message,
        }
        self.logs.append(entry)
        return entry


class LecturerObserver(ScheduleObserver):
    """Observer untuk dosen pengampu jadwal terkait."""

    def __init__(self, channel: str = "push") -> None:
        self.channel = channel
        self.logs: list[dict[str, Any]] = []

    def update(self, event: dict[str, Any]) -> dict[str, Any]:
        schedule = event.get("schedule", {})
        lecturer = schedule.get("dosen", "Dosen Pengampu")
        message = (
            f"[{self.channel.upper()} -> Dosen {lecturer}] "
            f"Event '{event.get('event_type')}' untuk mata kuliah '{schedule.get('matkul', schedule.get('id'))}' "
            f"({schedule.get('hari')}, {schedule.get('jam_mulai')}-{schedule.get('jam_selesai')}, "
            f"Ruang {schedule.get('ruangan')})."
        )
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "role": "lecturer",
            "channel": self.channel,
            "recipients": [lecturer],
            "event_type": event.get("event_type"),
            "message": message,
        }
        self.logs.append(entry)
        return entry


class AdminObserver(ScheduleObserver):
    """Observer untuk admin akademik guna memantau perubahan jadwal & tindak lanjut."""

    def __init__(self, channel: str = "sms") -> None:
        self.channel = channel
        self.logs: list[dict[str, Any]] = []

    def update(self, event: dict[str, Any]) -> dict[str, Any]:
        schedule = event.get("schedule", {})
        message = (
            f"[{self.channel.upper()} -> Admin Akademik] "
            f"Event '{event.get('event_type')}' pada jadwal ID '{schedule.get('id')}' "
            f"({schedule.get('matkul', '-')}, {schedule.get('hari')} {schedule.get('jam_mulai')}-{schedule.get('jam_selesai')}, "
            f"Ruang {schedule.get('ruangan')})."
        )
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "role": "admin",
            "channel": self.channel,
            "recipients": ["admin_akademik"],
            "event_type": event.get("event_type"),
            "message": message,
        }
        self.logs.append(entry)
        return entry


class ScheduleSubject:
    """Publisher / Notification Manager yang mengelola subscriber dan mengirim notifikasi."""

    def __init__(self) -> None:
        self._observers: list[ScheduleObserver] = []
        self.notification_logs: list[dict[str, Any]] = []

    def attach(self, observer: ScheduleObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: ScheduleObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_type: str, schedule_data: dict[str, Any]) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "event_type": event_type,
            "schedule": dict(schedule_data.get("schedule", schedule_data)),
            "students": schedule_data.get("students"),
        }
        sent_logs: list[dict[str, Any]] = []
        for observer in list(self._observers):
            entry = observer.update(payload)
            self.notification_logs.append(entry)
            sent_logs.append(entry)
        return sent_logs