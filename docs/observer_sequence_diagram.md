# Sequence / Alur Notifikasi Observer Pattern — Perubahan Jadwal Kuliah

## Peserta (Actors & Components)
- Admin / SchedulingService (pemicu perubahan jadwal)
- ScheduleSubject (publisher / subject)
- StudentObserver (subscriber mahasiswa — simulasi email)
- LecturerObserver (subscriber dosen — simulasi push)
- AdminObserver (subscriber admin akademik — simulasi SMS)
- Notification Log (pencatatan riwayat notifikasi)

## Alur Eksekusi
1. Registrasi Observer:
   Admin / SchedulingService memanggil `attach()` pada `ScheduleSubject` untuk mendaftarkan `StudentObserver`, `LecturerObserver`, dan `AdminObserver`.

2. Perubahan Jadwal:
   Saat jadwal diubah (misalnya hari, jam, atau ruangan berubah), sistem memanggil:
   `ScheduleSubject.notify("SCHEDULE_CHANGED", schedule_data)`

3. Penyebaran Notifikasi & Pencatatan Log:
   `ScheduleSubject` memanggil `update(event_type, schedule_data)` ke setiap observer yang terdaftar:
   - `StudentObserver` mengirim notifikasi (simulasi email) ke mahasiswa terdampak dan mencatatnya ke log.
   - `LecturerObserver` mengirim notifikasi (simulasi push) ke dosen terkait dan mencatatnya ke log.
   - `AdminObserver` mengirim notifikasi (simulasi SMS) ke admin akademik dan mencatatnya ke log.

4. Selesai:
   Seluruh notifikasi tercatat di log dan perubahan jadwal selesai diproses.