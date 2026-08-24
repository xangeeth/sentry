# Sentry - Automated Network Vulnerability Audit & Hardening Platform


## Overview

Sentry is a network infrastructure security, auditing, and compliance automation platform. It provides:
- **Hybrid Device Discovery**: Dual-protocol discovery supporting **Cisco RFC 8040 RESTCONF (YANG JSON)** on port `8080` with fallback to **Netmiko SSH CLI scraping** on port `2222`.
- **Vulnerability Intelligence**: Real-time integration with **NIST National Vulnerability Database (NVD) REST API v2.0** for live CVE correlation.
- **AI Security Brief & Remediation Engine**: Powered by local LLM (`llama3.1`) with a built-in fallback engine that synthesizes vendor-specific copy-paste CLI hardening scripts.
- **Web Dashboard**: React 19 single-page application with live fleet sync, CSV audit report generation, and interactive AI configuration assistant.

---

## Architecture

```text
               ┌──────────────────────────────────────────────────────────┐
               │              React 19 Fleet Dashboard (Frontend)         │
               │        (Fleet Overview, Universal Scanner, AI Assistant) │
               └────────────────────────────┬─────────────────────────────┘
                                            │ HTTP / REST API (Port 3000 -> 8000)
                                            ▼
               ┌──────────────────────────────────────────────────────────┐
               │                 FastAPI Backend Engine (:8000)           │
               │   (/api/v1/switches, /discover, /rescan, /scan, /analyze)│
               └───────────┬────────────────┬─────────────┬───────────────┘
                           │                │             │
        RESTCONF / SSH     │                │             │  NIST API / Ollama LLM
       ┌───────────────────┘                │             └───────────────────────────┐
       ▼                                    ▼                                         ▼
┌───────────────────────────┐    ┌────────────────────┐                    ┌──────────────────────┐
│ Sentry Switch Emulator    │    │ SQLite Database    │                    │ NIST NVD API (v2.0)  │
│ - 10 SSH Nodes (:2222)    │    │ (backend/sentry.db)│                    │ & AI Security Brain  │
│ - 1 RESTCONF Server (:8080│    └────────────────────┘                    │ (Local Ollama/Brain) │
└───────────────────────────┘                                              └──────────────────────┘
```

---

## Repository Structure

```
Sentry/
├── backend/
│   ├── brain.py             # AI Security Brief generator & fallback engine
│   ├── database.py          # SQLAlchemy SQLite & session setup
│   ├── discovery.py         # Hybrid discovery (RESTCONF RFC 8040 + Netmiko SSH)
│   ├── main.py              # FastAPI application & REST routing endpoints
│   ├── models.py            # SQLite schema definitions (Switch, HardwareLifecycle)
│   ├── requirements.txt     # Python backend dependencies
│   ├── scanner.py           # NIST NVD API v2.0 client
│   ├── seed_db.py           # Database seeder for hardware lifecycle baseline
│   └── switch_emulator.py   # Launcher forwarder to emulator/run_switches.py
├── emulator/
│   ├── configs/             # 10 Switch JSON configurations (switch1.json to switch10.json)
│   │   ├── switch1.json ... switch5.json   (Secure / Hardened Switch profiles)
│   │   └── switch6.json ... switch10.json  (Vulnerable / Bait Switch profiles)
│   ├── run_switches.py      # Multi-threaded SSH (port 2222) + RESTCONF (port 8080) emulator
│   └── test/
│       └── test_ai.py       # Ollama LLM connectivity test script
├── frontend/
│   ├── public/              # Static assets and index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIAssistant.js      # Plain-English to vendor CLI translation interface
│   │   │   ├── FleetDashboard.js   # Main fleet management table & AI model
│   │   │   ├── Sidebar.js          # Navigation sidebar
│   │   │   └── UniversalScanner.js # Live NIST NVD hardware CVE lookup tool
│   │   ├── api.js           # Frontend API client library
│   │   ├── App.js           # Core layout container
│   │   └── index.css        # Tailwind CSS imports & custom styles
│   └── package.json         # React frontend dependencies
├── .gitignore               # Comprehensive Git ignore rules
├── run_sentry.bat           # 1-Click launcher for Windows
└── README.md                # System documentation
```

---

## Quick Start:

### Prerequisites
- **Python 3.12+**
- **Node.js 18+ & npm**
- *(Optional)* **Ollama** with `llama3.1` model installed for local LLM generation.

---

### Option A: 1-Click Startup (Recommended for Windows)

Double-click `run_sentry.bat` or run in PowerShell:
```powershell
.\run_sentry.bat
```
*This automatically initializes the Python virtual environment, installs dependencies, and launches the Switch Emulator, FastAPI Backend, and React Frontend in synchronized windows.*

---

### Option B: Manual Step-by-Step Launch

#### 1. Setup Virtual Environment & Dependencies
```powershell
# Backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

#### 2. Start Switch Emulator (Terminal 1)
```powershell
.\.venv\Scripts\python.exe emulator/run_switches.py
```
*Emulator listens on `127.0.0.1:2222` (SSH) and `http://127.0.0.1:8080/restconf/data/native` (RESTCONF).*

#### 3. Start FastAPI Backend (Terminal 2)
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/`

#### 4. Start React Frontend Dashboard (Terminal 3)
```powershell
cd frontend
npm start
```
- Web UI: `http://localhost:3000`

---

## Emulated Switch Inventory

| Node | Hostname | IP / Port | Profile | Highlighted Flaws / Posture |
|:---|:---|:---|:---|:---|
| Node 1 | `Core-Cat9300-HQ` | `127.0.0.1:2222` | **SECURE** | SSH v2, AAA, Encrypted Secrets, HTTP Disabled |
| Node 2 | `Dist-Aruba2930-B1` | `127.0.0.2:2222` | **SECURE** | Hardened crypto keys, Telnet disabled |
| Node 3 | `Dist-JuniperEX-B2` | `127.0.0.3:2222` | **SECURE** | Junos security policies, RESTCONF enabled |
| Node 4 | `Edge-Cat3750-Fl1` | `127.0.0.4:2222` | **SECURE** | Port security active, BPDU guard enabled |
| Node 5 | `Edge-Arista7280` | `127.0.0.5:2222` | **SECURE** | EOS strict management ACLs |
| Node 6 | `Legacy-Cat2960-Lab` | `127.0.0.6:2222` | **VULNERABLE** | Plaintext enable password, Telnet allowed |
| Node 7 | `Branch-Cat3560-DMZ` | `127.0.0.7:2222` | **VULNERABLE** | `ip http server` enabled, SNMP `public` string |
| Node 8 | `DC-Cat4500-Storage` | `127.0.0.8:2222` | **VULNERABLE** | Smart Install / vStack enabled (CVE-2018-0171) |
| Node 9 | `OT-Cat2955-Factory` | `127.0.0.9:2222` | **VULNERABLE** | `no service password-encryption`, Telnet only |
| Node 10 | `Edge-PaloAlto-VPN` | `127.0.0.10:2222` | **VULNERABLE** | Outdated PAN-OS firmware with known remote CVEs |

*Authentication credentials for all emulator nodes: Username: `admin` / Password: `admin`*
