from app.observer import (
    AdminObserver,
    LecturerObserver,
    ScheduleSubject,
    StudentObserver,
)


def test_notify_all_stakeholders_and_record_logs():
    subject = ScheduleSubject()
    student_obs = StudentObserver(channel="email")
    lecturer_obs = LecturerObserver(channel="push")
    admin_obs = AdminObserver(channel="sms")

    subject.attach(student_obs)
    subject.attach(lecturer_obs)
    subject.attach(admin_obs)

    schedule_payload = {
        "schedule": {
            "id": "J1",
            "matkul": "Sistem Terdistribusi",
            "hari": "Selasa",
            "jam_mulai": "10:00",
            "jam_selesai": "12:00",
            "ruangan": "B202",
            "dosen": "Dr. Budi",
        },
        "students": ["MHS001", "MHS002"],
    }

    logs = subject.notify("SCHEDULE_CHANGED", schedule_payload)

    assert len(logs) == 3
    assert len(student_obs.logs) == 1
    assert len(lecturer_obs.logs) == 1
    assert len(admin_obs.logs) == 1
    assert len(subject.notification_logs) == 3

    assert student_obs.logs[0]["role"] == "student"
    assert student_obs.logs[0]["channel"] == "email"
    assert "SCHEDULE_CHANGED" in student_obs.logs[0]["message"]

    assert lecturer_obs.logs[0]["role"] == "lecturer"
    assert "Dr. Budi" in lecturer_obs.logs[0]["message"]

    assert admin_obs.logs[0]["role"] == "admin"
    assert "B202" in admin_obs.logs[0]["message"]


def test_detach_observer_stops_notification():
    subject = ScheduleSubject()
    student_obs = StudentObserver()
    admin_obs = AdminObserver()

    subject.attach(student_obs)
    subject.attach(admin_obs)
    subject.detach(admin_obs)

    subject.notify(
        "SCHEDULE_CANCELLED",
        {
            "id": "J9",
            "matkul": "Basis Data",
            "hari": "Rabu",
            "jam_mulai": "13:00",
            "jam_selesai": "15:00",
            "ruangan": "A101",
            "dosen": "Dr. Sari",
        },
    )

    assert len(student_obs.logs) == 1
    assert len(admin_obs.logs) == 0