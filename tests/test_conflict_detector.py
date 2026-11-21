from app.conflict_detector import detect_schedule_conflict


def test_detect_room_and_lecturer_conflicts():
    s1 = {
        "hari": "Senin",
        "jam_mulai": "08:00",
        "jam_selesai": "10:00",
        "ruangan": "A101",
        "dosen": "Dr. Budi",
        "matkul": "Kalkulus I",
    }
    s2 = {
        "hari": "Senin",
        "jam_mulai": "09:00",
        "jam_selesai": "11:00",
        "ruangan": "A101",
        "dosen": "Dr. Sari",
        "matkul": "Fisika Dasar",
    }
    s3 = {
        "hari": "Senin",
        "jam_mulai": "09:30",
        "jam_selesai": "11:30",
        "ruangan": "B202",
        "dosen": "Dr. Budi",
        "matkul": "Aljabar Linear",
    }

    conflicts = detect_schedule_conflict([s1, s2, s3])
    types = [c["type"] for c in conflicts]

    assert "room_conflict" in types
    assert "lecturer_conflict" in types
    assert len(conflicts) == 2


def test_no_conflict_when_adjacent_or_different_day():
    s1 = {
        "hari": "Senin",
        "jam_mulai": "08:00",
        "jam_selesai": "10:00",
        "ruangan": "A101",
        "dosen": "Dr. Budi",
    }
    s2 = {
        "hari": "Senin",
        "jam_mulai": "10:00",
        "jam_selesai": "12:00",
        "ruangan": "A101",
        "dosen": "Dr. Budi",
    }
    s3 = {
        "hari": "Selasa",
        "jam_mulai": "08:00",
        "jam_selesai": "10:00",
        "ruangan": "A101",
        "dosen": "Dr. Budi",
    }

    assert detect_schedule_conflict([s1, s2, s3]) == []


def test_optional_time_overlap_only():
    s1 = {
        "hari": "Rabu",
        "jam_mulai": "13:00",
        "jam_selesai": "15:00",
        "ruangan": "A101",
        "dosen": "Dr. Budi",
    }
    s2 = {
        "hari": "Rabu",
        "jam_mulai": "14:00",
        "jam_selesai": "16:00",
        "ruangan": "C303",
        "dosen": "Dr. Rina",
    }

    assert detect_schedule_conflict([s1, s2], include_time_overlap_only=False) == []
    overlaps = detect_schedule_conflict([s1, s2], include_time_overlap_only=True)
    assert len(overlaps) == 1
    assert overlaps[0]["type"] == "time_overlap"