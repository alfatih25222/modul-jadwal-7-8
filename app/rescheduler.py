from dataclasses import dataclass
from typing import Any


@dataclass
class SlotCandidate:
    hari: str
    jam: str          # contoh: "08:00-10:00" atau "13:00-15:00"
    ruangan: str
    kapasitas: int


def _parse_start_minutes(jam: str) -> int:
    start_str = jam.split("-", 1)[0].strip()
    hours, minutes = map(int, start_str.split(":"))
    return hours * 60 + minutes


def _parse_range_minutes(jam: str) -> tuple[int, int]:
    start_str, end_str = [part.strip() for part in jam.split("-", 1)]
    sh, sm = map(int, start_str.split(":"))
    eh, em = map(int, end_str.split(":"))
    return sh * 60 + sm, eh * 60 + em


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def recommend_alternative_schedules(
    conflicting_schedule: dict[str, Any],
    available_slots: list[dict[str, Any]],
    existing_schedules: list[dict[str, Any]] | None = None,
    max_suggestions: int = 3,
) -> list[dict[str, str]]:
    """
    Merekomendasikan maksimal 3 alternatif jadwal yang:
    1. Kapasitas ruangan mencukupi jumlah mahasiswa
    2. Tidak bentrok dengan jadwal dosen (maupun slot ruangan terpakai)
    3. Prioritas pagi/siang (minimal disruption untuk mahasiswa)
    """
    enrolled = int(conflicting_schedule.get("jumlah_mahasiswa", conflicting_schedule.get("enrolled", 0)))
    dosen = conflicting_schedule.get("dosen")
    existing = existing_schedules or []

    candidates: list[tuple[int, dict[str, str]]] = []

    for slot in available_slots:
        hari = str(slot["hari"])
        jam = str(slot["jam"])
        ruangan = str(slot["ruangan"])
        kapasitas = int(slot["kapasitas"])

        if kapasitas < enrolled:
            continue

        slot_range = _parse_range_minutes(jam)

        # Cek bentrok dengan jadwal dosen pada hari & jam yang sama
        lecturer_busy = False
        room_busy = False
        for sched in existing:
            if str(sched.get("hari")) != hari:
                continue
            sched_jam = sched.get("jam")
            if not sched_jam:
                continue
            if _overlaps(slot_range, _parse_range_minutes(str(sched_jam))):
                if dosen and sched.get("dosen") == dosen:
                    lecturer_busy = True
                    break
                if sched.get("ruangan") == ruangan:
                    room_busy = True
                    break

        if lecturer_busy or room_busy:
            continue

        start_mins = _parse_start_minutes(jam)
        # Skor prioritas: pagi (<= 11:30) paling diutamakan, lalu siang (<= 15:00), lalu sore
        if start_mins <= 11 * 60 + 30:
            period_label = "pagi"
            priority_score = 0
        elif start_mins <= 15 * 60:
            period_label = "siang"
            priority_score = 1
        else:
            period_label = "sore"
            priority_score = 2

        same_day_penalty = 0 if hari == conflicting_schedule.get("hari") else 1
        sort_key = (priority_score, same_day_penalty, start_mins)

        reason = (
            f"Kapasitas {ruangan} ({kapasitas}) cukup untuk {enrolled} mahasiswa, "
            f"tidak bentrok dengan jadwal dosen, dan slot {period_label} meminimalkan gangguan kuliah."
        )

        candidates.append(
            (
                sort_key[0] * 10000 + sort_key[1] * 1000 + sort_key[2],
                {
                    "hari": hari,
                    "jam": jam,
                    "ruangan": ruangan,
                    "reason": reason,
                },
            )
        )

    candidates.sort(key=lambda item: item[0])
    return [item[1] for item in candidates[:max_suggestions]]