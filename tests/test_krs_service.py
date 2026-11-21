from app.krs_service import KrsService


def test_invalidate_krs_when_schedule_changes():
    krs = KrsService()
    krs.enroll_krs("KRS-1", "MHS001", "J1")
    krs.enroll_krs("KRS-2", "MHS002", "J1")
    krs.enroll_krs("KRS-3", "MHS003", "J2")

    invalidated = krs.invalidate_by_schedule_change(
        "J1", reason="Perubahan jam/ruangan jadwal J1"
    )

    assert len(invalidated) == 2
    assert krs.get_krs("KRS-1").status == "INVALIDATED"
    assert krs.get_krs("KRS-2").status == "INVALIDATED"
    assert krs.get_krs("KRS-1").invalidation_reason == "Perubahan jam/ruangan jadwal J1"
    assert krs.get_krs("KRS-3").status == "VALID"
