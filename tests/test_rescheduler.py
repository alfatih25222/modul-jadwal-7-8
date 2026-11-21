from app.rescheduler import recommend_alternative_schedules


def test_recommend_top_3_prioritizing_morning_and_capacity():
    conflicting = {
        "mata_kuliah": "Kalkulus I",
        "hari": "Senin",
        "jam": "08:00-10:00",
        "ruangan": "A101",
        "dosen": "Dr. Budi",
        "jumlah_mahasiswa": 40,
    }
    slots = [
        {"hari": "Rabu", "jam": "15:30-17:30", "ruangan": "B202", "kapasitas": 50},
        {"hari": "Selasa", "jam": "08:00-10:00", "ruangan": "A102", "kapasitas": 45},
        {"hari": "Kamis", "jam": "09:00-11:00", "ruangan": "A103", "kapasitas": 30},  # kapasitas kurang
        {"hari": "Selasa", "jam": "10:00-12:00", "ruangan": "B201", "kapasitas": 60},
        {"hari": "Jumat", "jam": "08:00-10:00", "ruangan": "C101", "kapasitas": 50},
    ]
    existing = [
        {"hari": "Jumat", "jam": "08:00-10:00", "ruangan": "C101", "dosen": "Dr. Budi"}  # dosen bentrok
    ]

    suggestions = recommend_alternative_schedules(conflicting, slots, existing_schedules=existing)

    assert len(suggestions) == 3
    assert all({"hari", "jam", "ruangan", "reason"} <= set(s.keys()) for s in suggestions)
    # Slot pagi kapasitas cukup & dosen bebas harus muncul duluan
    assert suggestions[0]["hari"] == "Selasa"
    assert suggestions[0]["jam"] == "08:00-10:00"
    assert suggestions[0]["ruangan"] == "A102"