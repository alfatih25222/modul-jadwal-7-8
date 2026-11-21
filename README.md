## Struktur Proyek

```text
modul-jadwal-7-8/
├── app/
│   ├── conflict_detector.py   # Deteksi bentrok rentang waktu menggunakan Interval Tree
│   ├── krs_service.py         # Integrasi & invalidasi KRS saat jadwal berubah
│   ├── observer.py            # Implementasi Observer Pattern (Student, Lecturer, Admin)
│   ├── rescheduler.py         # Rekomendasi jadwal alternatif berbasis AI
│   ├── scheduling_service.py  # CRUD jadwal, validasi kapasitas, deteksi bentrok & notifikasi
│   └── storage.py             # Penyimpanan dan pemuatan state ke/dari file JSON
├── docs/
│   └── observer_sequence_diagram.md  # Dokumentasi alur notifikasi Observer Pattern
├── tests/
│   ├── test_conflict_detector.py
│   ├── test_krs_service.py
│   ├── test_observer.py
│   ├── test_rescheduler.py
│   ├── test_scheduling_service.py
│   └── test_storage.py
└── README.md
```