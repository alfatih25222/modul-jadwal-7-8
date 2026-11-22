from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.conflict_detector import detect_schedule_conflict
from app.krs_service import KrsService
from app.observer import (
    AdminObserver,
    LecturerObserver,
    ScheduleSubject,
    StudentObserver,
)
from app.rescheduler import recommend_alternative_schedules
from app.scheduling_service import (
    ScheduleNotFoundError,
    ScheduleValidationError,
    SchedulingService,
)
from app.storage import load_service_state, save_service_state

DEFAULT_STATE_PATH = Path("data/schedule_state.json")

app = FastAPI(
    title="Sistem Manajemen Jadwal Kuliah API",
    version="1.0.0",
    description="Antarmuka web/API (Swagger UI) untuk manajemen jadwal kuliah, deteksi bentrok, rekomendasi slot, KRS, dan notifikasi observer.",
)


def _create_subject() -> ScheduleSubject:
    subject = ScheduleSubject()
    subject.attach(StudentObserver(channel="email"))
    subject.attach(LecturerObserver(channel="push"))
    subject.attach(AdminObserver(channel="sms"))
    return subject


subject = _create_subject()
service = SchedulingService(subject=subject)
krs_service = KrsService()


# --- Pydantic Models ---

class RoomCapacityRequest(BaseModel):
    ruangan: str = Field(..., examples=["A101"])
    kapasitas: int = Field(..., gt=0, examples=[45])


class ScheduleCreateRequest(BaseModel):
    id: str = Field(..., examples=["JDW-01"])
    matkul: str = Field(..., examples=["Pemrograman Web"])
    hari: str = Field(..., examples=["Senin"])
    jam_mulai: str = Field(..., examples=["08:00"])
    jam_selesai: str = Field(..., examples=["10:00"])
    ruangan: str = Field(..., examples=["A101"])
    dosen: str = Field(..., examples=["Budi Santoso"])
    enrolled: int = Field(default=0, ge=0, examples=[35])
    students: list[str] | None = Field(default=None, examples=[["MHS-001", "MHS-002"]])
    extra: dict[str, Any] = Field(default_factory=dict)


class ScheduleUpdateRequest(BaseModel):
    updates: dict[str, Any] = Field(..., examples=[{"jam_mulai": "10:00", "jam_selesai": "12:00"}])


class ConflictCheckRequest(BaseModel):
    schedules: list[dict[str, Any]]
    include_time_overlap_only: bool = False


class RescheduleRequest(BaseModel):
    conflicting_schedule: dict[str, Any]
    available_slots: list[dict[str, Any]]
    existing_schedules: list[dict[str, Any]] | None = None
    max_suggestions: int = Field(default=3, ge=1, le=10)


class KrsEnrollRequest(BaseModel):
    krs_id: str = Field(..., examples=["KRS-001"])
    student_id: str = Field(..., examples=["MHS-001"])
    schedule_id: str = Field(..., examples=["JDW-01"])


class KrsInvalidateRequest(BaseModel):
    schedule_id: str = Field(..., examples=["JDW-01"])
    reason: str = Field(default="Jadwal kuliah berubah")


class StatePathRequest(BaseModel):
    file_path: str = Field(default=str(DEFAULT_STATE_PATH))


# --- Helper ---

def _merge_schedule_payload(payload: ScheduleCreateRequest) -> dict[str, Any]:
    data = payload.model_dump(exclude={"extra"})
    if data.get("students") is None:
        data.pop("students", None)
    data.update(payload.extra)
    return data


# --- Endpoints: Jadwal & Ruangan ---

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Sistem Manajemen Jadwal Kuliah API aktif.",
        "docs": "/docs",
    }


@app.post("/api/rooms/capacity", summary="Atur Kapasitas Ruangan")
def set_room_capacity(payload: RoomCapacityRequest) -> dict[str, Any]:
    try:
        service.set_room_capacity(payload.ruangan, payload.kapasitas)
        return {
            "message": "Kapasitas ruangan berhasil disimpan.",
            "room_capacities": dict(service.room_capacities),
        }
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/rooms/capacity", summary="Lihat Kapasitas Ruangan")
def list_room_capacities() -> dict[str, int]:
    return dict(service.room_capacities)


@app.post("/api/jadwal", status_code=201, summary="Buat Jadwal Kuliah")
def create_schedule(payload: ScheduleCreateRequest) -> dict[str, Any]:
    try:
        created = service.create_schedule(_merge_schedule_payload(payload))
        return {"message": "Jadwal berhasil dibuat.", "data": created}
    except (ScheduleValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jadwal", summary="Daftar Semua Jadwal Kuliah")
def list_schedules() -> dict[str, Any]:
    items = service.list_schedules()
    return {"total": len(items), "data": items}


@app.get("/api/jadwal/{schedule_id}", summary="Detail Jadwal Berdasarkan ID")
def get_schedule(schedule_id: str) -> dict[str, Any]:
    try:
        return {"data": service.get_schedule(schedule_id)}
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/jadwal/{schedule_id}", summary="Ubah Jadwal Kuliah")
def update_schedule(schedule_id: str, payload: ScheduleUpdateRequest) -> dict[str, Any]:
    try:
        updated = service.update_schedule(schedule_id, payload.updates)
        return {"message": "Jadwal berhasil diperbarui.", "data": updated}
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ScheduleValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/jadwal/{schedule_id}", summary="Hapus Jadwal Kuliah")
def delete_schedule(schedule_id: str) -> dict[str, Any]:
    try:
        deleted = service.delete_schedule(schedule_id)
        return {"message": "Jadwal berhasil dihapus.", "data": deleted}
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- Endpoints: Deteksi Bentrok & Rekomendasi ---

@app.post("/api/jadwal/cek-bentrok", summary="Deteksi Bentrok Jadwal")
def check_conflicts(payload: ConflictCheckRequest) -> dict[str, Any]:
    try:
        conflicts = detect_schedule_conflict(
            payload.schedules,
            include_time_overlap_only=payload.include_time_overlap_only,
        )
        return {
            "has_conflict": len(conflicts) > 0,
            "total_conflicts": len(conflicts),
            "conflicts": conflicts,
        }
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/jadwal/rekomendasi", summary="Rekomendasi Jadwal Alternatif")
def recommend_schedules(payload: RescheduleRequest) -> dict[str, Any]:
    try:
        suggestions = recommend_alternative_schedules(
            conflicting_schedule=payload.conflicting_schedule,
            available_slots=payload.available_slots,
            existing_schedules=payload.existing_schedules,
            max_suggestions=payload.max_suggestions,
        )
        return {
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
        }
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- Endpoints: KRS ---

@app.post("/api/krs/enroll", status_code=201, summary="Daftarkan KRS Mahasiswa")
def enroll_krs(payload: KrsEnrollRequest) -> dict[str, Any]:
    record = krs_service.enroll_krs(payload.krs_id, payload.student_id, payload.schedule_id)
    return {"message": "KRS berhasil didaftarkan.", "data": asdict(record)}


@app.get("/api/krs/{krs_id}", summary="Lihat Status KRS Berdasarkan ID")
def get_krs(krs_id: str) -> dict[str, Any]:
    try:
        record = krs_service.get_krs(krs_id)
        return {"data": asdict(record)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/krs/by-schedule/{schedule_id}", summary="Daftar KRS Berdasarkan Jadwal")
def list_krs_by_schedule(schedule_id: str) -> dict[str, Any]:
    records = [asdict(r) for r in krs_service.list_krs_by_schedule(schedule_id)]
    return {"total": len(records), "data": records}


@app.post("/api/krs/invalidate", summary="Invalidate KRS Akibat Perubahan Jadwal")
def invalidate_krs(payload: KrsInvalidateRequest) -> dict[str, Any]:
    affected = [
        asdict(r)
        for r in krs_service.invalidate_by_schedule_change(
            schedule_id=payload.schedule_id,
            reason=payload.reason,
        )
    ]
    return {
        "message": "KRS terdampak berhasil di-invalidate.",
        "total_affected": len(affected),
        "data": affected,
    }


# --- Endpoints: Notifikasi Observer ---

@app.get("/api/notifications", summary="Lihat Log Notifikasi Perubahan Jadwal")
def list_notifications() -> dict[str, Any]:
    logs = list(subject.notification_logs)
    return {"total": len(logs), "data": logs}


# --- Endpoints: Simpan & Muat State ---

@app.post("/api/state/simpan", summary="Simpan State Jadwal ke JSON")
def save_state(payload: StatePathRequest) -> dict[str, Any]:
    try:
        saved_path = save_service_state(service, payload.file_path)
        return {
            "message": "State berhasil disimpan.",
            "file_path": str(saved_path),
        }
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/state/muat", summary="Muat State Jadwal dari JSON")
def load_state(payload: StatePathRequest) -> dict[str, Any]:
    global service
    try:
        loaded = load_service_state(payload.file_path, subject=service.subject)
        service = loaded
        return {
            "message": "State berhasil dimuat.",
            "total_schedules": len(service.list_schedules()),
            "room_capacities": dict(service.room_capacities),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File tidak ditemukan: {payload.file_path}") from exc
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc