# 🛡️ IDS Pemantau Ujian Online (HIDS)

> **Host-based Intrusion Detection System** untuk memantau integritas peserta ujian online secara real-time.

Sistem ini terdiri dari tiga komponen utama yang bekerja secara terpadu:
- **Backend Server** — REST API & WebSocket berbasis FastAPI + PostgreSQL
- **Desktop Agent** — Program Python ringan yang berjalan di komputer peserta ujian
- **Dashboard Web (PWA)** — Antarmuka pemantauan real-time untuk pengawas ujian

---

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
- [Cara Menjalankan](#-cara-menjalankan)
- [Konfigurasi Environment](#-konfigurasi-environment)
- [Endpoint API](#-endpoint-api)
- [Struktur Proyek](#-struktur-proyek)

---

## ✨ Fitur Utama

### Desktop Agent
| Sensor | Deskripsi |
|--------|-----------|
| 🪟 **Window Tracker** | Mendeteksi perpindahan fokus ke aplikasi lain selama ujian |
| 📋 **Clipboard Monitor** | Memantau aktivitas salin-tempel yang mencurigakan |
| ⚙️ **Process Scanner** | Mendeteksi proses/aplikasi terlarang yang berjalan di latar belakang |
| 💓 **Heartbeat** | Mengirim sinyal rutin ke server untuk membuktikan agen masih aktif |

### Backend Server
- **Autentikasi JWT** — Login peserta dengan PIN sesi + username/password
- **Keamanan HMAC** — Setiap data telemetri diverifikasi tanda tangannya sebelum disimpan
- **WebSocket Real-time** — Pengawas menerima notifikasi anomali secara langsung
- **Riwayat Log** — Semua anomali tersimpan di database PostgreSQL

### Dashboard Web (PWA)
- Dapat diakses dari browser (termasuk mobile)
- Menampilkan daftar peserta aktif beserta status heartbeat
- Menampilkan feed log anomali secara real-time via WebSocket
- Dapat diinstal sebagai Progressive Web App

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                    KOMPUTER PESERTA UJIAN                    │
│                                                             │
│   ┌───────────────────────────────────────────────────┐    │
│   │              Desktop Agent (Python)                │    │
│   │  ┌─────────────┐ ┌──────────────┐ ┌───────────┐  │    │
│   │  │WindowTracker│ │ClipboardMonit│ │ProcScanner│  │    │
│   │  └──────┬──────┘ └──────┬───────┘ └─────┬─────┘  │    │
│   │         └───────────────┴───────────────┘         │    │
│   │                         │ HMAC-signed POST         │    │
│   └─────────────────────────┼──────────────────────────┘    │
└─────────────────────────────┼───────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Backend Server   │
                    │  (FastAPI + uvicorn)│
                    │                   │
                    │  /api/v1/auth      │
                    │  /api/v1/telemetry │
                    │  ws://…/ws         │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼──────┐  ┌────▼────┐  ┌─────▼──────┐
       │  PostgreSQL  │  │ WebSocket│  │  PWA / Web │
       │   Database   │  │ Clients  │  │  Dashboard │
       └─────────────┘  └─────────┘  └────────────┘
```

---

## 🔧 Teknologi yang Digunakan

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — Framework web async Python
- **SQLAlchemy 2.0** (Async) — ORM database
- **Alembic** — Migrasi skema database
- **PostgreSQL 15** — Database utama
- **asyncpg** — Driver PostgreSQL async
- **PyJWT** — Token autentikasi JSON Web Token
- **Loguru** — Logging terstruktur

### Desktop Agent
- **Python 3.x** + `tkinter` — GUI login ringan
- `threading` — Menjalankan sensor secara paralel
- `requests` / `websockets` — Komunikasi ke backend

### Dashboard Web
- **HTML5 + CSS3 + Vanilla JS** — Tanpa framework frontend
- **PWA** (Progressive Web App) — Manifest + Service Worker
- **WebSocket API** — Pembaruan real-time

### Infrastruktur
- **Docker & Docker Compose** — Kontainerisasi backend + database

---

## 🚀 Cara Menjalankan

### Prasyarat
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) terinstal
- Python 3.10+ (untuk menjalankan Desktop Agent)

### 1. Clone Repository

```bash
git clone https://github.com/Subiasa/IDS_UjianOnline.git
cd IDS_UjianOnline
```

### 2. Jalankan Backend dengan Docker Compose

```bash
docker-compose up --build -d
```

Server akan berjalan di `http://localhost:8000`.

### 3. Inisialisasi Data Awal (Opsional)

Kunjungi endpoint berikut di browser untuk membuat data dummy:

```
http://localhost:8000/seed
```

Ini akan membuat:
- **Username:** `testuser`
- **Password:** *(apa saja)*
- **PIN Sesi:** `1234`

### 4. Akses Dashboard Web

Buka browser dan kunjungi:

```
http://localhost:8000/mobile/dashboard.html
```

### 5. Jalankan Desktop Agent

```bash
cd agent/desktop
pip install -r requirements.txt
python src/main.py
```

Login menggunakan PIN sesi, username, dan password yang telah dibuat.

---


---

## 📡 Endpoint API

### Autentikasi
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/v1/auth/login` | Login peserta (PIN + username + password) |

### Telemetri (memerlukan tanda tangan HMAC di header `X-Signature`)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/v1/telemetry/log` | Mengirim log anomali dari agen |
| `POST` | `/api/v1/telemetry/heartbeat` | Mengirim sinyal heartbeat |
| `GET` | `/api/v1/telemetry/history` | Mengambil riwayat log anomali |
| `GET` | `/api/v1/telemetry/participants` | Mengambil daftar peserta aktif |

### WebSocket
| Endpoint | Deskripsi |
|----------|-----------|
| `ws://localhost:8000/ws` | Koneksi real-time untuk dashboard pengawas |

---

## 📁 Struktur Proyek

```
IDS_pemantau/
├── docker-compose.yml          # Orkestrasi Docker (backend + database)
│
├── backend/                    # Backend Server (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini             # Konfigurasi migrasi Alembic
│   ├── migrations/             # File migrasi database
│   ├── static/                 # File Dashboard Web (PWA)
│   │   ├── index.html          # Halaman login peserta (PWA)
│   │   ├── dashboard.html      # Halaman dashboard pengawas
│   │   ├── dashboard.js
│   │   ├── dashboard.css
│   │   ├── api.js
│   │   ├── sensors.js
│   │   ├── ui.js
│   │   ├── manifest.json       # PWA manifest
│   │   └── service-worker.js   # PWA service worker
│   └── app/
│       ├── main.py             # Entry point FastAPI
│       └── api/
│           ├── routers/
│           │   ├── auth.py
│           │   ├── telemetri.py
│           │   └── websocket.py
│           └── services/
│
└── agent/
    └── desktop/                # Desktop Agent (Python)
        ├── requirements.txt
        └── src/
            ├── main.py         # Entry point agen
            ├── config.py       # Konfigurasi URL server & kunci
            ├── logger.py       # Setup Loguru
            ├── network/
            │   └── api_client.py   # HTTP client ke backend
            └── core/
                └── sensors/
                    ├── window_tracker.py   # Sensor perpindahan jendela
                    ├── clipboard_mon.py    # Sensor clipboard
                    └── process_scanner.py  # Sensor proses berjalan
```

---

## 👤 Pengembang

Dikembangkan oleh **Subiasa** sebagai proyek studi implementasi sistem keamanan berbasis host (HIDS) untuk lingkungan ujian online.

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan studi dan edukasi.
