# Sistem Manajemen Jadwal Kuliah

Proyek modular berbasis Python dengan pendekatan *clean architecture* untuk mengelola jadwal kuliah, mendeteksi bentrok ruangan/dosen, memvalidasi kapasitas ruangan, mengirim notifikasi perubahan jadwal menggunakan *Observer Pattern*, serta menyimpan/memuat *state* ke format JSON.

## Struktur Proyek

```text
modul-jadwal-7-8/
├── app/
│   ├── conflict_detector.py   # Deteksi bentrok rentang waktu menggunakan Interval Tree
│   ├── observer.py            # Implementasi Observer Pattern (Student, Lecturer, Admin)
│   ├── scheduling_service.py  # CRUD jadwal, validasi kapasitas, deteksi bentrok & notifikasi
│   └── storage.py             # Penyimpanan dan pemuatan state ke/dari file JSON
├── tests/
│   ├── test_conflict_detector.py
│   ├── test_observer.py
│   ├── test_scheduling_service.py
│   └── test_storage.py
└── README.md