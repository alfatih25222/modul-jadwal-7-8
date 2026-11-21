from app.scheduling_service import SchedulingService
from app.storage import load_service_state, save_service_state


def test_save_and_load_service_state(tmp_path):
    service = SchedulingService(room_capacities={"A101": 45})
    service.create_schedule(
        {
            "id": "J1",
            "matkul": "Pemrograman Python",
            "hari": "Senin",
            "jam_mulai": "08:00",
            "jam_selesai": "10:00",
            "ruangan": "A101",
            "dosen": "Dr. Budi",
            "enrolled": 30,
        }
    )

    target_file = tmp_path / "jadwal_state.json"
    save_service_state(service, target_file)
    assert target_file.exists()

    restored = load_service_state(target_file)
    assert restored.room_capacities == {"a101": 45}
    schedules = restored.list_schedules()
    assert len(schedules) == 1
    assert schedules[0]["id"] == "J1"
    assert schedules[0]["matkul"] == "Pemrograman Python"