from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _IntervalNode:
    start: int
    end: int
    max_end: int
    schedule: dict[str, Any]
    left: _IntervalNode | None = None
    right: _IntervalNode | None = None


class _IntervalTree:
    """Interval tree sederhana untuk mencari jadwal dengan rentang jam yang overlap."""

    def __init__(self) -> None:
        self.root: _IntervalNode | None = None

    def insert(self, start: int, end: int, schedule: dict[str, Any]) -> None:
        self.root = self._insert(self.root, start, end, schedule)

    def _insert(
        self,
        node: _IntervalNode | None,
        start: int,
        end: int,
        schedule: dict[str, Any],
    ) -> _IntervalNode:
        if node is None:
            return _IntervalNode(start=start, end=end, max_end=end, schedule=schedule)

        if start < node.start:
            node.left = self._insert(node.left, start, end, schedule)
        else:
            node.right = self._insert(node.right, start, end, schedule)

        if end > node.max_end:
            node.max_end = end
        if node.left and node.left.max_end > node.max_end:
            node.max_end = node.left.max_end
        if node.right and node.right.max_end > node.max_end:
            node.max_end = node.right.max_end

        return node

    def query_overlap(self, start: int, end: int) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        self._query(self.root, start, end, results)
        return results

    def _query(
        self,
        node: _IntervalNode | None,
        start: int,
        end: int,
        results: list[dict[str, Any]],
    ) -> None:
        if node is None:
            return

        if node.left is not None and node.left.max_end > start:
            self._query(node.left, start, end, results)

        if node.start < end and start < node.end:
            results.append(node.schedule)

        if node.right is not None and node.start < end:
            self._query(node.right, start, end, results)


def _to_minutes(jam_str: str) -> int:
    """Konversi format 'HH:MM' menjadi menit sejak 00:00."""
    parts = jam_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Format jam tidak valid: '{jam_str}' (gunakan 'HH:MM')")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Nilai jam di luar rentang: '{jam_str}'")
    return hour * 60 + minute


def detect_schedule_conflict(
    schedules: list[dict[str, Any]],
    include_time_overlap_only: bool = False,
) -> list[dict[str, Any]]:
    """
    Mendeteksi bentrok jadwal berdasarkan hari, jam, ruangan, dan dosen
    dengan memanfaatkan interval tree per hari untuk pencarian jam overlap.

    Setiap item input diharapkan memiliki keys:
    - hari (str)
    - jam_mulai (str 'HH:MM')
    - jam_selesai (str 'HH:MM')
    - ruangan (str)
    - dosen (str)
    """
    trees_by_day: dict[str, _IntervalTree] = {}
    conflicts: list[dict[str, Any]] = []
    seen_pairs: set[tuple[int, int, str]] = set()

    indexed_schedules: list[tuple[int, dict[str, Any], int, int]] = []
    for idx, sched in enumerate(schedules):
        start_min = _to_minutes(sched["jam_mulai"])
        end_min = _to_minutes(sched["jam_selesai"])
        if end_min <= start_min:
            raise ValueError(
                f"jam_selesai ({sched['jam_selesai']}) harus lebih besar dari jam_mulai ({sched['jam_mulai']})"
            )
        indexed_schedules.append((idx, sched, start_min, end_min))

    for idx, sched, start_min, end_min in indexed_schedules:
        day = str(sched["hari"]).strip().lower()
        tree = trees_by_day.setdefault(day, _IntervalTree())

        overlapping_candidates = tree.query_overlap(start_min, end_min)
        for other in overlapping_candidates:
            other_idx: int = other["_idx"]
            pair_key_base = (min(idx, other_idx), max(idx, other_idx))

            matched_types: list[str] = []
            if str(sched["ruangan"]).strip().lower() == str(other["ruangan"]).strip().lower():
                matched_types.append("room_conflict")
            if str(sched["dosen"]).strip().lower() == str(other["dosen"]).strip().lower():
                matched_types.append("lecturer_conflict")

            if not matched_types and include_time_overlap_only:
                matched_types.append("time_overlap")

            for c_type in matched_types:
                full_key = (pair_key_base[0], pair_key_base[1], c_type)
                if full_key not in seen_pairs:
                    seen_pairs.add(full_key)
                    s1 = schedules[pair_key_base[0]]
                    s2 = schedules[pair_key_base[1]]
                    conflicts.append(
                        {
                            "type": c_type,
                            "affected_schedules": [s1, s2],
                        }
                    )

        entry_with_meta = dict(sched)
        entry_with_meta["_idx"] = idx
        tree.insert(start_min, end_min, entry_with_meta)

    return conflicts