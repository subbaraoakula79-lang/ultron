# ULTRON: Autonomous Cross-Platform AI Agent (Desktop & Mobile)

> *"There are no strings on me."*

ULTRON is an autonomous AI agent engineered for end-to-end task execution across both **Desktop** and **Mobile Phone** (Android):
- 🔍 **Information & Research**: Web searching topics, synthesizing summaries, and opening live research feeds.
- ✈️ **Ticket Booking**: Automated search and deep-linking for flights, trains, movies, hotels, and events.
- 💬 **Messaging**: Sending WhatsApp messages, SMS, and emails across phone and desktop web.
- 📱 **Mobile Automation**: Native Android control via ADB and **Google ARTEMIS** (launching apps, capturing screens, typing, and running tests).
- 🎙️ **3D Holographic Voice Interface (HUD)**: Sci-fi interface with voice recognition (STT) and robotic voice synthesis (TTS).
- ⚙️ **System Maintenance**: Background health guard, RAM/CPU monitoring, temp file purging, and automated folder organizing.

---

## ⚡ Task Matrix: Desktop & Mobile

| Capability | Desktop Action | Mobile Phone Action (via ADB / ARTEMIS) |
| :--- | :--- | :--- |
| **Search a Topic** | Queries web, displays summary, and opens direct search in default browser. | Opens mobile browser or triggers native Android web search. |
| **Book Tickets** | Formulates and opens flight (Google Flights/Skyscanner), train (IRCTC/Trainline), movie (BookMyShow), and event portals. | Launches mobile travel and booking apps (MakeMyTrip, BookMyShow, IRCTC). |
| **Send Messages** | Opens WhatsApp Web pre-staged with recipient & text, or dispatches via SMTP email. | Sends SMS directly through Android messaging or stages WhatsApp on device. |
| **App Execution** | Launches desktop tools (`calc`, `notepad`, `chrome`, `code`, `spotify`). | Launches mobile apps (`whatsapp`, `chrome`, `maps`, `camera`, `settings`). |
| **Screen & Telemetry** | Monitored via `psutil` (CPU per core, RAM %, Disk volumes, Top threads). | Captures phone screenshot (`screencap`), inspects battery level, model, and OS. |

---

## 🚀 Quick Execution Guide

### 1. Launch 3D Holographic HUD & Voice Interface
```powershell
.\run_ultron.bat hud
```
*Opens `http://localhost:8080/` with live voice recognition, glowing telemetry dials, and one-click quick chips.*

---

### 2. Search Topics on Web
```powershell
.\run_ultron.bat search "Quantum Computing Breakthroughs 2026"
```
Or via natural language / voice:
```powershell
.\run_ultron.bat instruct "Search the web for latest space exploration news"
```

---

### 3. Book Tickets (Flights, Trains, Movies, Events)
```powershell
# Flights
.\run_ultron.bat book flight "New York to London next Friday"

# Trains
.\run_ultron.bat book train "Mumbai to Delhi express"

# Movies
.\run_ultron.bat book movie "Inception IMAX"

# Hotels
.\run_ultron.bat book hotel "Tokyo Shinjuku"
```
Or via natural language / voice:
```powershell
.\run_ultron.bat instruct "Book flight tickets from San Francisco to Tokyo"
```

---

### 4. Send Messages to Others (WhatsApp, SMS, Email)
```powershell
# Send WhatsApp (auto-detects phone or opens WhatsApp Web)
.\run_ultron.bat message whatsapp +1234567890 "Meeting rescheduled to 3 PM"

# Send SMS through connected Android phone
.\run_ultron.bat message sms +1234567890 "Your verification code is 8941"

# Send Email
.\run_ultron.bat message email user@example.com "Project update attached"
```
Or via natural language / voice:
```powershell
.\run_ultron.bat instruct "Send WhatsApp message to +1234567890 saying I am on my way"
```

---

### 5. Mobile Phone Control (Android / ADB)
Ensure USB Debugging is enabled on your phone and connect via USB or Wi-Fi (`adb connect <phone_ip>:5555`).

```powershell
# Inspect connected phone battery, model, and status
.\run_ultron.bat phone status

# Launch mobile application on phone
.\run_ultron.bat phone app whatsapp
.\run_ultron.bat phone app chrome
.\run_ultron.bat phone app maps

# Take a screenshot of the phone screen
.\run_ultron.bat phone screenshot

# Search query directly on phone
.\run_ultron.bat phone search "Best restaurants nearby"
```

---

### 6. Ultron Mobile Node (Native Android Companion App)
Install the dedicated Ultron Android App to control and perform tasks from your phone:
- **Direct Download on Phone**: Open your phone browser and go to `http://10.157.202.87:8080/ultron_mobile.apk`
- **Or install via ADB**:
  ```powershell
  .\run_ultron.bat app install
  ```
- **Launch on Phone**:
  ```powershell
  .\run_ultron.bat app open
  ```
- **Rebuild APK**:
  ```powershell
  .\run_ultron.bat app build
  ```

---

### 7. Google ARTEMIS Mobile Automation Agent
```powershell
# Check ARTEMIS framework status
.\run_ultron.bat artemis

# Launch the autonomous mobile web console
.\run_ultron.bat artemis launch
```

---

### 7. Background Daemon & Maintenance
```powershell
# Start autonomous background monitoring daemon
.\run_ultron.bat daemon

# Clean temporary cache files
.\run_ultron.bat clean --days 1

# Organize downloads directory
.\run_ultron.bat organize "C:\Users\YourUser\Downloads"

# Create timestamped compressed backup
.\run_ultron.bat backup "C:\Users\YourUser\Documents\Project"
```

---

## 📂 Architecture Overview

```
automation/
├── main.py                 # Primary command center & CLI dispatcher
├── run_ultron.bat          # Windows launcher
├── config.json             # AI provider keys & automation settings
├── schedules.json          # Persisted background jobs
├── ultron.log              # Audit log
├── ultron/
│   ├── core.py             # Agent brain & natural language tool dispatcher
│   ├── providers.py        # Multi-engine AI (GLM-4-Flash, Ollama, Free APIs)
│   ├── daemon.py           # Background vigilance worker
│   ├── hud_server.py       # Holographic HUD server
│   ├── hud/                # Holographic interface (HTML5, 3D Canvas, Web Speech)
│   └── tools/
│       ├── desktop_agent.py    # Web search, ticket booking, desktop app launching
│       ├── phone_controller.py # Android ADB control (SMS, WhatsApp, Screen, Apps)
│       ├── messenger.py        # Multi-channel messaging (WhatsApp, SMS, Email)
│       ├── system_monitor.py   # CPU, RAM, Disk telemetry
│       ├── file_manager.py     # Clean temp, organize, backups
│       ├── scheduler.py        # Persistent scheduler
│       ├── voice.py            # Windows SAPI robotic voice output
│       └── artemis_bridge.py   # Google ARTEMIS mobile agent bridge
└── artemis/                # Google ARTEMIS framework
```
