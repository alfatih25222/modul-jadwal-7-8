import pytest

from app.observer import AdminObserver, LecturerObserver, ScheduleSubject, StudentObserver
from app.scheduling_service import (
    ScheduleNotFoundError,
    ScheduleValidationError,
    SchedulingService,
)


def test_crud_schedule_success():
    service = SchedulingService(room_capacities={"A101": 45, "B202": 30})

    created = service.create_schedule(
        {
            "id": "J1",
            "matkul": "Kalkulus I",
            "hari": "Senin",
            "jam_mulai": "08:00",
            "jam_selesai": "10:00",
            "ruangan": "A101",
            "dosen": "Dr. Budi",
            "enrolled": 40,
        }
    )
    assert created["id"] == "J1"
    assert len(service.list_schedules()) == 1

    updated = service.update_schedule("J1", {"jam_mulai": "09:00", "jam_selesai": "11:00"})
    assert updated["jam_mulai"] == "09:00"
    assert service.get_schedule("J1")["jam_selesai"] == "11:00"

    deleted = service.delete_schedule("J1")
    assert deleted["id"] == "J1"
    assert service.list_schedules() == []


def test_reject_when_capacity_exceeded():
    service = SchedulingService(room_capacities={"A101": 35})

    with pytest.raises(ScheduleValidationError, match="Kapasitas ruangan"):
        service.create_schedule(
            {
                "id": "J1",
                "matkul": "Kalkulus I",
                "hari": "Senin",
                "jam_mulai": "08:00",
                "jam_selesai": "10:00",
                "ruangan": "A101",
                "dosen": "Dr. Budi",
                "enrolled": 40,
            }
        )


def test_reject_when_conflict_occurs():
    service = SchedulingService(
        room_capacities={"A101": 50, "B202": 50},
        initial_schedules=[
            {
                "id": "J1",
                "matkul": "Kalkulus I",
                "hari": "Senin",
                "jam_mulai": "08:00",
                "jam_selesai": "10:00",
                "ruangan": "A101",
                "dosen": "Dr. Budi",
                "enrolled": 30,
            }
        ],
    )

    with pytest.raises(ScheduleValidationError, match="bentrok"):
        service.create_schedule(
            {
                "id": "J2",
                "matkul": "Basis Data",
                "hari": "Senin",
                "jam_mulai": "09:00",
                "jam_selesai": "11:00",
                "ruangan": "A101",
                "dosen": "Dr. Sari",
                "enrolled": 25,
            }
        )


def test_get_or_delete_missing_schedule_raises():
    service = SchedulingService()
    with pytest.raises(ScheduleNotFoundError):
        service.get_schedule("TIDAK_ADA")
    with pytest.raises(ScheduleNotFoundError):
        service.delete_schedule("TIDAK_ADA")


def test_service_notifies_observers_on_create_update_delete():
    subject = ScheduleSubject()
    student_obs = StudentObserver()
    lecturer_obs = LecturerObserver()
    admin_obs = AdminObserver()

    subject.attach(student_obs)
    subject.attach(lecturer_obs)
    subject.attach(admin_obs)

    service = SchedulingService(room_capacities={"A101": 50}, subject=subject)

    service.create_schedule(
        {
            "id": "J10",
            "matkul": "Arsitektur Perangkat Lunak",
            "hari": "Kamis",
            "jam_mulai": "13:00",
            "jam_selesai": "15:00",
            "ruangan": "A101",
            "dosen": "Dr. Andi",
            "enrolled": 35,
            "students": ["MHS101", "MHS102"],
        }
    )
    service.update_schedule("J10", {"jam_mulai": "14:00", "jam_selesai": "16:00"})
    service.delete_schedule("J10")

    events = [log["event_type"] for log in subject.notification_logs]
    assert events.count("SCHEDULE_CREATED") == 3
    assert events.count("SCHEDULE_UPDATED") == 3
    assert events.count("SCHEDULE_DELETED") == 3
    assert len(student_obs.logs) == 3
    assert len(lecturer_obs.logs) == 3
    assert len(admin_obs.logs) == 3