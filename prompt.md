
# PRODUCT REQUIREMENT DOCUMENT (PRD)

**Nama Projek:** Implementasi Host-Based Intrusion Detection System (HIDS) Berorientasikan Pengalaman Pengguna (UX) Untuk Ujian Online

**Versi Projek:** 1.0

**Tarikh:** Mei 2026

**Status Dokumen:** Ditandatangani (Locked Architecture)

---

## 1. Pengenalan & Objektif Projek

### 1.1 Latar Belakang

Ujian dalam talian sering kali terdedah kepada isu integriti akademik (penipuan). Kekangan utama sistem pengawasan sedia ada adalah kesukaran konfigurasi (menyulitkan pengguna) dan ketiadaan sokongan rentas platform yang inklusif untuk peserta yang hanya memiliki telefon pintar (*smartphone*).

### 1.2 Objektif Utama

* Membina sistem pemantauan tingkah laku pasif (HIDS) berprestasi tinggi yang tidak mengganggu perkakasan hos (*non-intrusive*).
* Menyediakan sokongan dwi-platform: Aplikasi mudah alih (*mobile app*) dan perisian komputer (*desktop executable*).
* Mewujudkan proses persediaan sifar hambatan (*zero-friction UX*) untuk peserta ujian.
* Menyokong fleksibiliti kaedah ujian melalui dua mod: **Opsi A** (Pautan Pihak Ketiga seperti Google Form berpembungkus iFrame) dan **Opsi B** (Enjin Ujian Tempatan).

---

## 2. Arkitektur Sistem & Aliran Data Teknis

Sistem ini menggunakan seni bina **Multi-Tenant Examination Broker** berasaskan komunikasi masa nyata (WebSockets) dan pengesahan kuki/JWT yang selamat.

### 2.1 Aliran Proses Permulaan (Handshake Awal)

1. **Peserta** mengakses portal web ujian $\rightarrow$ Masuk menggunakan PIN Sesi.
2. **Portal Web** menyemak status konfigurasi sesi pada pangkalan data (Sama ada Opsi A atau Opsi B).
3. Layar portal dikunci: Menampilkan arahan ringkas bagi mengaktifkan Agen Pemantau.
4. **Agen HIDS** (Laptop/Mobile) diaktifkan oleh peserta $\rightarrow$ Agen menghantar isyarat *heartbeat* pertama ke backend FastAPI.
5. **Portal Web** mengesan isyarat keaktifan tersebut secara automatik $\rightarrow$ Tombol "Mulai Ujian" bertukar hijau dan boleh diakses.

---

## 3. Spesifikasi Keperluan Fungsian (Functional Requirements)

Sesuai dengan garis masa pengerjaan, fungsian sistem dibahagi kepada tiga fasa utama:

### FASA 1: Membangun Sistem (System Core Building)

#### 3.1.1 Ejen Pemantau Komputer (Desktop Agent - Python)

* **Keperluan UI:** Berjalan secara portabel tanpa memerlukan pemasangan (*no-installation portable file*). Beroperasi dalam latar belakang dengan ikon status minimal pada *system tray*.
* **Sensor Deteksi:**
* **Window Tracker:** Mengimbas judul tetingkap (*window title*) yang aktif setiap 1 saat menggunakan pustaka seperti `pygetwindow`/`pywin32`.
* **Clipboard Monitor:** Mengesan aktiviti penyalinan atau penampalan teks secara luar biasa pada memori OS menggunakan `pyperclip`.
* **Process Scanner:** Memeriksa senarai proses latar belakang yang sedang berjalan berdasarkan senarai hitam (*blacklist*) seperti aplikasi komunikasi (Discord, WhatsApp, Telegram) menggunakan `psutil`.


* **Modul Rangkaian:** Menghantar data log kecurangan dan isyarat *heartbeat* setiap 10 saat ke server utama menggunakan kaedah HTTP POST tak senkron (*asynchronous*).

#### 3.1.2 Ejen Pemantau Mudah Alih (Mobile Agent -   PWA)

* **Keperluan UI:** Berasaskan web mudah alih berkeupayaan tinggi (PWA) untuk mengelakkan keperluan memuat turun fail APK/App Store yang rumit.
* **Sensor Deteksi:**
* **App Lifecycle Observer:** Memanfaatkan fungsi `WidgetsBindingObserver` atau API Javascript `visibilitychange`. Jika peserta menekan butang Home, menukar tab browser, atau membuka panel notifikasi, sistem serta-merta mengesan status *blur* atau *backgrounded*.
* **Screen Constraints:** Mengesan mod skrin terbahagi (*split-screen*) atau tingkap terapung (*floating windows*).



#### 3.1.3 Komponen Backend & Pangkalan Data (FastAPI & PostgreSQL)

* **API Gateway:** Menyediakan endpoint pengesahan token `/api/v1/auth/agent-login` dan penerimaan log telemetri `/api/v1/telemetry/log`.
* **Antisabotaj (Anti-Tampering):** Mengesahkan integriti data log yang dihantar oleh ejen klien menggunakan fungsi tanda tangan kriptografi HMAC-SHA256 untuk mengelakkan manipulasi menggunakan alat seperti Postman.

---

### FASA 2: Pengujian Sistem (System Testing)

Skema pengujian wajib merangkumi kriteria-kriteria berikut untuk menjamin kebolehpercayaan sistem sebelum diserahkan kepada petugas:

| Jenis Ujian | Kaedah & Senario Pengujian | Hasil Yang Diharapkan |
| --- | --- | --- |
| **Ujian Unit Sensor** | Menjalankan ejen pemantau pada laptop ujian kemudian sengaja membuka aplikasi Google Chrome dan menaip perkataan "ChatGPT" pada enjin carian. | Sistem berjaya menangkap anomali `WINDOW_SWITCHING` dengan tepat tanpa ralat. |
| **Ujian Beban (Stress Test)** | Menembak server FastAPI dengan simulasi 500 paket log telemetri serentak menggunakan peralatan ujian prestasi (cth: Locust atau Apache JMeter). | Server kekal stabil, kadar ralat 0%, dan masa tindak balas API di bawah 200ms. |
| **Ujian Ketahanan Rangkaian** | Memutuskan sambungan WiFi pada laptop peserta ujian selama 30 saat semasa simulasi ujian sedang berlangsung. | Ejen HIDS tidak ranap (*crash*); log disimpan dalam simpanan tempatan (*local storage*) dan dihantar semula sebaik sahaja talian internet pulih. |

---

### FASA 3: Pembuatan Antarmuka Petugas (Admin UI Development)

Dasbor bagi petugas (Pengawas) dibina dengan fokus terhadap kepantasan penilaian situasi secara masa nyata.

#### 3.3.1 Komunikasi WebSocket Backend

* Server FastAPI menyediakan saluran WebSocket `/api/v1/ws/monitor` khas untuk akaun pengawas ujian.
* Setiap log anomali yang sah dimasukkan ke dalam pangkalan data akan dipancarkan (*broadcast*) secara langsung ke saluran WebSocket ini dalam masa kurang daripada 0.5 saat.

#### 3.3.2 Reka Bentuk Antarmuka Petugas (Dashboard Pengawas)

* **Paparan Ringkasan Status Visual:** Menyediakan kad petunjuk berasaskan warna (*Color-coded Alert Cards*) untuk menapis status peserta ujian secara pantas:
* **Hijau (Selamat):** Peserta fokus pada skrin ujian, isyarat *heartbeat* normal.
* **Jingga (Amaran Sederhana):** Kehilangan fokus tetingkap atau aplikasi ujian berada dalam latar belakang seketika.
* **Merah (Bahaya/Pelanggaran Tinggi):** Membuka aplikasi terlarang, menyalin teks tidak dibenarkan, atau aplikasi pemantau dimatikan secara paksa (`AGENT_DISCONNECTED`).


* **Panel Kawalan Tindakan Pantas (Action Panel):** Petugas diberikan butang fungsi khusus bersebelahan dengan nama peserta untuk:
1. Menghantar mesej amaran secara langsung ke skrin peranti peserta.
2. Membatalkan atau mengunci sesi ujian peserta secara serta-merta sekiranya bukti kecurangan digital telah disahkan.



---

## 4. Keperluan Bukan Fungsian (Non-Functional Requirements)

* **Sekuriti & Privasi:** Ejen HIDS dilarang keras merakam visual layar (screenshot) penuh atau menjejaki papan kekunci (*keylogger*) secara menyeluruh bagi mematuhi etika privasi data peribadi peserta. Sistem hanya membaca parameter metadata sistem operasi sahaja.
* **Kecekapan Sumber Jentera:** Penggunaan memori oleh ejen komputer semasa berjalan di latar belakang mestilah di bawah 50 MB RAM dan penggunaan CPU di bawah 2%.
* **Skalabiliti Saiz Data:** Log telemetri yang dihantar harus dioptimumkan dalam format fail JSON dengan saiz purata setiap penghantaran adalah kurang daripada 2 KB bagi meminimumkan penggunaan kuota internet peserta.

---

PRD ini mengunci seluruh spesifikasi teknikal sistem ujian anda. Dokumen ini sedia dijadikan rujukan utama dalam pembangunan fail kod pertama bagi skrip sensor pemantauan komputer anda.


![alt text](image-1.png)

Alur Sinkronisasi "Start-up" (Langkah Demi Langkah)

    Tahap 1: Aktivasi Agen HIDS (Laptop/Mobile)
    Peserta membuka aplikasi HIDS Pemantau. Begitu aktif, agen ini langsung mendaftarkan diri ke server dan mendapatkan Session_Token. Status peserta di server saat ini: "Monitoring Active" (Pemantauan Aktif).

    Tahap 2: Pembukaan Web/Aplikasi Ujian
    Ketika peserta membuka halaman web ujian untuk login, sistem web ujian akan menembak API ke server backend untuk mengecek: "Apakah ID peserta ini status HIDS-nya sudah 'Monitoring Active'?"

        Jika Sudah: Tombol "Mulai Ujian" akan terbuka dan berwarna hijau. Peserta bisa masuk ke soal.

        Jika Belum: Halaman ujian terkunci, muncul peringatan: "Aplikasi Pemantau Belum Dijalankan. Silakan aktifkan aplikasi pemantau Anda terlebih dahulu."

    Tahap 3: Ujian Berjalan & Live Monitoring
    Selama ujian berlangsung (misal 90 menit), agen HIDS terus mengirimkan data secara pasif. Di sisi pengawas, mereka tidak perlu melihat layar satu per satu peserta, melainkan cukup melihat Dashboard Anomali.

Topologi Arsitektur Sistem Global
![alt text](image.png)

hids-ujian-online/
│
├── backend-server/   # Kode Backend Utama (FastAPI + PostgreSQL)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py # Titik masuk utama aplikasi (FastAPI instance)
│   │   ├── config.py              # Pengaturan database, JWT, dan env variables
│   │   ├── database.py        # Koneksi dan inisialisasi SQLAlchemy/PostgreSQL
│   │   ├── models.py  # Definisi tabel database (Sesi Ujian, Log Anomali, User)
│   │   ├── schemas.py       # Validasi skema data Pydantic (Request/Response)
│   │   ├── routers/                # Pemisahan Endpoint API
│   │   │   ├── auth.py             # API Autentikasi agen dan peserta
│   │   │   ├── telemetri.py        # API Penerima Log Telemetri & Heartbeat
│   │   │   └── ujian.py          # API Manajemen sesi (Opsi A Wrapper & Opsi B)
│   │   └── utils/
│   │       └── security.py     # Logika verifikasi signature HMAC-SHA256 & JWT
│   ├── requirements.txt            # Dependensi library backend
│   └── .env           # Berkas rahasia konfigurasi server (DB_URL, SECRET_KEY)
│
├── agent-desktop/                  # Agen HIDS khusus Laptop (Python)
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # Skrip utama pembuka/jembatan aplikasi
│   │   ├── config.py               # Konfigurasi endpoint server & token lokal
│   │   ├── core/                   # Logika Sensor HIDS
│   │   │   ├── window_tracker.py   # Deteksi pindah jendela (pygetwindow)
│   │   │   ├── clipboard_mon.py    # Deteksi perubahan salin-tempel (pyperclip)
│   │   │   └── process_scanner.py  # Pemindaian blacklist aplikasi (psutil)
│   │   └── network/
│   │       └── api_client.py       # Pengirim data log & Heartbeat via Requests
│   ├── build.py               # Skrip otomasi kompilasi ke .exe (PyInstaller)
│   └── requirements.txt            # Dependensi library desktop agent
│
├── agent-mobile/                   # Agen HIDS khusus Mobile (Flutter)
│   ├── lib/
│   │   ├── main.dart               # Titik masuk aplikasi Flutter
│   │   ├── models/                 # Model data log anomali
│   │   ├── services/
│   │   │   ├── api_service.dart    # Komunikasi HTTP ke server backend
│   │   │   └── hids_service.dart   # Lifecycle listener & Focus loss detector
│   │   └── views/                  # UI Aplikasi jembatan mobile sebelum ujian
│   └── pubspec.yaml                # Dependensi library Flutter
│



Sisi Server & Penyimpanan (Backend & Storage)
API Gateway & Backend--->FastAPI (Python)
Menyediakan endpoint REST API yang sangat cepat dan asinkron (async/await) untuk menerima ribuan traffic log hantaman dari klien tanpa crash.

Database Utama--->PostgreSQL (dengan kolom JSONB)
Menyimpan data terstruktur peserta, sesi ujian, dan log anomali yang fleksibel di dalam kolom JSONB berkecepatan tinggi.

Cache & Queue (Opsional untuk skala besar)--->redis
Bertindak sebagai penyangga (buffer) jika ribuan log masuk bersamaan sebelum ditulis ke PostgreSQL, menjaga server tetap stabil.


Flow Pengerjaan Proyek (Milestones Roadmap)

Sesuai dengan alur kerja yang Anda inginkan, pengerjaan akan dibagi menjadi 3 fase besar:

FASE 1: Membangun Sistem (System Core Building)
Fokus pada fungsionalitas inti dan pengumpulan data sensor.

    Backend Foundation: Membuat skema database PostgreSQL menggunakan FastAPI untuk menampung data log kecurangan dan status keaktifan agen.

    Desktop Core Development: Menulis skrip Python untuk melacak judul jendela aktif (pygetwindow) dan memindai proses latar belakang (psutil).

    Mobile Core Development: Mengonfigurasi Lifecycle Listener pada Flutter untuk menangkap status ketika aplikasi berpindah ke latar belakang (backgrounded).

    API Integration: Menyambungkan pengiriman telemetri dari agen laptop dan mobile menuju server FastAPI secara asinkron.
