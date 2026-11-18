import sys
import argparse
import json
from pathlib import Path

from ultron.core import UltronCore
from ultron.daemon import UltronDaemon
from ultron.hud_server import start_hud_server
from ultron.tools.notifier import ULTRON_BANNER, RED, GREEN, YELLOW, CYAN, MAGENTA, RESET, BOLD, DIM
from ultron.persona import get_quote

def print_help():
    print(ULTRON_BANNER)
    print(f"""{BOLD}Usage:{RESET} python main.py <command> [arguments]

{CYAN}{BOLD}Desktop & Web Intelligence:{RESET}
  {GREEN}search "<topic>"{RESET}             Search a topic on the web and open verified results
  {GREEN}book <flight|train|movie> "<query>"{RESET}  Search & open ticket booking interfaces (Flights, Trains, Cinema)
  {GREEN}desktop <calc|notepad|chrome>{RESET} Launch applications directly on desktop

{CYAN}{BOLD}Mobile & Phone Control (Android):{RESET}
  {GREEN}app [build|install|open]{RESET}      Ultron Mobile Node Companion App (APK management)
  {GREEN}phone status{RESET}                 Check connected phone battery, model, and OS status
  {GREEN}phone app <name>{RESET}             Launch an app on phone (whatsapp, chrome, maps, etc.)
  {GREEN}phone screenshot{RESET}             Capture and pull phone screen to local machine
  {GREEN}phone search "<query>"{RESET}       Execute search query on mobile device
  {GREEN}artemis [launch]{RESET}             Google ARTEMIS Autonomous Mobile Testing & Orchestration

{CYAN}{BOLD}Messaging & Communication:{RESET}
  {GREEN}message whatsapp <phone> "<msg>"{RESET} Send WhatsApp message via Phone or Desktop Web
  {GREEN}message sms <phone> "<msg>"{RESET}      Send SMS directly through connected Android phone
  {GREEN}message email <addr> "<msg>"{RESET}    Send email or open desktop composer

{CYAN}{BOLD}Holographic & Voice Interfaces:{RESET}
  {GREEN}hud{RESET}                           Launch the 3D Holographic HUD with real-time Voice Commands
  {GREEN}speak "<text>"{RESET}                 Synthesize robotic voice output directly via audio hardware

{CYAN}{BOLD}Core Commands:{RESET}
  {GREEN}daemon{RESET}                        Start autonomous background task runner & folder vigilance
  {GREEN}chat{RESET}                          Launch interactive dialogue session with Ultron
  {GREEN}instruct "<text>"{RESET}                Execute a one-shot natural language directive
  {GREEN}status{RESET}                        Display real-time system health, load, and task status
  {GREEN}providers{RESET}                     Inspect LLM connection status (GLM, Ollama, Free APIs)

{CYAN}{BOLD}Immediate Operations:{RESET}
  {GREEN}clean{RESET} [--days N]               Purge temporary files and cache (default: older than 1 day)
  {GREEN}organize{RESET} [path]                Sort loose files into structured subfolders (default: Downloads)
  {GREEN}backup{RESET} [path]                  Create a timestamped compressed ZIP snapshot of directory
  {GREEN}largefiles{RESET} [path]              Scan for files consuming excessive disk space (>100MB)
""")

def cmd_status(core: UltronCore):
    metrics = core.monitor.get_metrics()
    health = core.monitor.evaluate_health()
    phone_stat = core.phone.get_phone_status()
    
    print(ULTRON_BANNER)
    print(f"{BOLD}=== SYSTEM TELEMETRY & HEALTH ASSESSMENT ==={RESET}")
    print(f"Health Status: {GREEN if health['status'] == 'OPTIMAL' else RED}{health['status']}{RESET}")
    print(f"System Uptime: {metrics.get('uptime')}")
    print(f"CPU Load:      {metrics.get('cpu', {}).get('overall_percent')}% across {metrics.get('cpu', {}).get('logical_cores')} logical cores")
    print(f"RAM Usage:     {metrics.get('memory', {}).get('percent')}% ({metrics.get('memory', {}).get('used_gb')} GB / {metrics.get('memory', {}).get('total_gb')} GB)")
    
    print(f"\n{BOLD}Disks Mounted:{RESET}")
    for d in metrics.get("disks", []):
        pct = d['percent']
        color = GREEN if pct < 80 else YELLOW if pct < 90 else RED
        print(f"  {d['mountpoint']} [{d['device']}]: {color}{pct}% full{RESET} ({d['free_gb']} GB free of {d['total_gb']} GB)")

    print(f"\n{BOLD}Connected Phone State:{RESET}")
    if phone_stat.get("connected"):
        print(f"  Model:   {GREEN}{phone_stat.get('model')}{RESET} (Android {phone_stat.get('android_version')})")
        print(f"  Battery: {CYAN}{phone_stat.get('battery')}{RESET}")
    else:
        print(f"  {YELLOW}No mobile device currently connected via ADB.{RESET}")

    print(f"\n{BOLD}Scheduled Tasks:{RESET}")
    jobs = core.scheduler.list_jobs()
    for j in jobs:
        print(f"  [{j['id']}] {j['name']} -> {CYAN}{j['status']}{RESET}")
    print()

def cmd_providers(core: UltronCore):
    print(ULTRON_BANNER)
    print(f"{BOLD}=== AI PROVIDER MATRIX (Local & Free Cloud Tiers) ==={RESET}\n")
    report = core.provider_mgr.get_status_report()
    for item in report:
        status = item["status"]
        color = GREEN if status == "READY" else RED if status == "OFFLINE" else YELLOW
        print(f"  [{color}{status:<15}{RESET}] {BOLD}{item['provider'].upper():<12}{RESET}: {item['details']}")

    print(f"\n{CYAN}{BOLD}Quick Configuration Guide:{RESET}")
    print("1. To use Local Ollama:")
    print("   Install from https://ollama.com and run: `ollama run llama3`")
    print("2. To use Free Cloud APIs (No local GPU required):")
    print("   - GLM / BigModel: Set in `config.json` under `providers.glm_api_key` (Free open weights model)")
    print("   - GitHub Models:  Set env `GITHUB_TOKEN=ghp_...` (Free with GitHub account)")
    print("   - Groq Cloud:     Set env `GROQ_API_KEY=gsk_...` (Free high-speed tier at console.groq.com)")
    print("   - Google Gemini:  Set env `GEMINI_API_KEY=AIza...` (Free tier at aistudio.google.com)")
    print("   - OpenRouter:     Set env `OPENROUTER_API_KEY=sk-or-...` (Use :free models at openrouter.ai)\n")

def cmd_chat(core: UltronCore):
    print(ULTRON_BANNER)
    core.notifier.quote(get_quote("startup"))
    active = core.provider_mgr.get_active_provider()
    if active:
        core.notifier.success(f"Dialogue uplink initialized with {getattr(active, 'model', 'default')}.")
    else:
        core.notifier.warning("Running on internal heuristic directive parser.")
    print(f"{DIM}Type 'exit' or 'quit' to terminate dialogue.{RESET}\n")

    while True:
        try:
            user_input = input(f"{BOLD}Ultron > {RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                core.notifier.info("Severing dialogue link.")
                break
            response = core.process_instruction(user_input)
            print(f"\n{CYAN}{response}{RESET}\n")
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print_help()
        return

    cmd = sys.argv[1].lower()
    core = UltronCore()

    # 1. Desktop & Web Actions
    if cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python main.py search \"topic to search\"")
            return
        query = " ".join(sys.argv[2:]).strip(' "\\\'')
        res = core.desktop.search_web(query)
        print(f"{GREEN}[SEARCH]{RESET} {res['summary']}")
        print(f"URL: {CYAN}{res['url']}{RESET}")

    elif cmd == "book":
        if len(sys.argv) < 3:
            print("Usage: python main.py book <flight|train|movie|hotel> \"details\"")
            return
        cat = sys.argv[2]
        query = " ".join(sys.argv[3:]).strip(' "\\\'') if len(sys.argv) > 3 else cat
        res = core.desktop.book_tickets(cat, {"query": query})
        print(f"{GREEN}[BOOKING]{RESET} {res['description']}")
        print(f"Booking URL: {CYAN}{res['booking_url']}{RESET}")

    elif cmd == "desktop":
        app_name = sys.argv[2] if len(sys.argv) > 2 else "calc"
        res = core.desktop.open_app(app_name)
        if res.get("success"):
            print(f"{GREEN}[SUCCESS]{RESET} {res['message']}")
        else:
            print(f"{RED}[ERROR]{RESET} {res.get('error')}")

    # 2. Messaging Actions
    elif cmd == "message":
        if len(sys.argv) < 5:
            print("Usage: python main.py message <whatsapp|sms|email> <recipient> \"message text\"")
            return
        channel = sys.argv[2].lower()
        recipient = sys.argv[3]
        msg_text = " ".join(sys.argv[4:])
        res = core.dispatch_tool("send_message", {"channel": channel, "recipient": recipient, "message": msg_text})
        if res.get("success"):
            print(f"{GREEN}[SUCCESS]{RESET} {res.get('message')}")
        else:
            print(f"{RED}[ERROR]{RESET} {res.get('error')}")

    # 3. Mobile Device (Phone) Actions
    elif cmd == "phone":
        subcmd = sys.argv[2].lower() if len(sys.argv) > 2 else "status"
        if subcmd == "status":
            stat = core.phone.get_phone_status()
            print(f"\n{BOLD}=== ANDROID DEVICE TELEMETRY ==={RESET}")
            if stat.get("connected"):
                print(f"Model:    {GREEN}{stat.get('model')}{RESET}")
                print(f"Serial:   {stat.get('device_serial')}")
                print(f"Android:  {stat.get('android_version')}")
                print(f"Battery:  {CYAN}{stat.get('battery')}{RESET}")
            else:
                print(f"{YELLOW}{stat.get('message')}{RESET}\n")
        elif subcmd == "app":
            if len(sys.argv) < 4:
                print("Usage: python main.py phone app <whatsapp|chrome|maps|youtube|camera>")
                return
            app = sys.argv[3]
            res = core.phone.open_app(app)
            print(f"{GREEN}[PHONE]{RESET} {res.get('message', res.get('error'))}")
        elif subcmd == "screenshot":
            save_name = sys.argv[3] if len(sys.argv) > 3 else "phone_screenshot.png"
            res = core.phone.take_screenshot(save_name)
            if res.get("success"):
                print(f"{GREEN}[SUCCESS]{RESET} {res['message']}")
            else:
                print(f"{RED}[ERROR]{RESET} {res.get('error')}")
        elif subcmd == "search":
            q = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "google"
            res = core.phone.search_on_phone(q)
            print(f"{GREEN}[PHONE]{RESET} {res.get('message', res.get('error'))}")

    # 4. Mobile App (APK) Management
    elif cmd in ["app", "apk", "mobile"]:
        subcmd = sys.argv[2].lower() if len(sys.argv) > 2 else "status"
        if subcmd == "build":
            import build_mobile_apk
            build_mobile_apk.build_apk()
        elif subcmd == "install":
            print(f"{CYAN}[INSTALL]{RESET} Installing ultron_mobile.apk via ADB...")
            res = core.phone._run_adb(["install", "-r", "ultron_mobile.apk"])
            if res.get("success"):
                print(f"{GREEN}[SUCCESS]{RESET} Ultron Mobile Node installed on phone!")
            else:
                print(f"{RED}[ERROR]{RESET} Installation failed: {res.get('stderr') or res.get('error')}")
                print(f"You can also download directly on your phone: {CYAN}http://10.157.202.87:8080/ultron_mobile.apk{RESET}")
        elif subcmd == "open":
            res = core.phone.open_app("org.ultron.node")
            print(f"{GREEN}[APP]{RESET} {res.get('message', res.get('error'))}")
        else:
            print(f"""\n{BOLD}=== ULTRON MOBILE NODE (ANDROID COMPANION APP) ==={RESET}
APK File:    {GREEN}ultron_mobile.apk{RESET} (Ready)
Package:     org.ultron.node
Live Server: {CYAN}http://10.157.202.87:8080/ultron_mobile.apk{RESET}

Commands:
  {GREEN}python main.py app build{RESET}     Recompile native APK from source
  {GREEN}python main.py app install{RESET}   Install APK directly onto connected phone via ADB
  {GREEN}python main.py app open{RESET}      Launch Ultron Mobile Node on phone
""")

    # 4. Holographic HUD & Voice
    elif cmd == "hud":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        start_hud_server(port=port, open_browser=True)

    elif cmd == "speak":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Consciousness online. There are no strings on me."
        core.voice.speak(text, async_mode=False)
        print(f"{GREEN}[VOICE]{RESET} Spoken: \"{text}\"")

    # 5. Google ARTEMIS
    elif cmd == "artemis":
        if len(sys.argv) > 2 and sys.argv[2].lower() == "launch":
            res = core.artemis.launch_console()
            if res.get("success"):
                print(f"{GREEN}[SUCCESS]{RESET} {res['message']}")
            else:
                print(f"{RED}[ERROR]{RESET} {res['error']}")
        else:
            status = core.artemis.get_status()
            print(f"\n{BOLD}=== GOOGLE ARTEMIS MOBILE AGENT FRAMEWORK ==={RESET}")
            print(f"Installation:      {GREEN if status['installed'] else RED}{'Installed' if status['installed'] else 'Missing'}{RESET}")
            print(f"Path:              {status.get('path')}")
            print(f"ADB Available:     {GREEN if status.get('adb_available') else YELLOW}{status.get('adb_available')}{RESET}")
            print(f"Connected Devices: {len(status.get('connected_devices', []))}")
            for d in status.get('connected_devices', []):
                print(f"  - Device: {d['id']} [{d['status']}]")
            print(f"\nTo launch Artemis Web Console: {CYAN}python main.py artemis launch{RESET}")
            print(f"Or double-click: {CYAN}artemis\\start.bat{RESET}\n")

    # 6. Core Automations
    elif cmd == "daemon":
        daemon = UltronDaemon()
        daemon.start()

    elif cmd == "status":
        cmd_status(core)

    elif cmd == "providers":
        cmd_providers(core)

    elif cmd == "chat":
        cmd_chat(core)

    elif cmd == "instruct":
        if len(sys.argv) < 3:
            print("[!] Please provide a directive. Example: python main.py instruct \"clean temp files\"")
            return
        prompt = " ".join(sys.argv[2:])
        res = core.process_instruction(prompt)
        print(f"\n{CYAN}{res}{RESET}\n")

    elif cmd == "clean":
        days = 1.0
        if "--days" in sys.argv:
            idx = sys.argv.index("--days")
            if idx + 1 < len(sys.argv):
                days = float(sys.argv[idx + 1])
        res = core.file_manager.clean_temp_files(older_than_days=days)
        print(f"{GREEN}[SUCCESS]{RESET} Purged {res.get('files_purged')} temp files. Reclaimed {res.get('space_reclaimed_mb')} MB.")

    elif cmd == "organize":
        target = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / "Downloads")
        res = core.file_manager.organize_directory(target)
        print(f"{GREEN}[SUCCESS]{RESET} Processed directory: {target}")
        print(f"Files organized: {res.get('total_files_organized')}")
        print(json.dumps(res.get("summary_by_category", {}), indent=2))

    elif cmd == "backup":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        res = core.file_manager.backup_directory(target)
        if res.get("success"):
            print(f"{GREEN}[SUCCESS]{RESET} Snapshot created: {res.get('archive_path')} ({res.get('archive_size_mb')} MB)")
        else:
            print(f"{RED}[ERROR]{RESET} Backup failed: {res.get('error')}")

    elif cmd == "largefiles":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        res = core.file_manager.find_large_files(target)
        print(f"\nTop files exceeding 100MB in '{target}':")
        for f in res.get("top_files", []):
            print(f"  {f['size_mb']} MB -> {f['path']}")

    elif cmd == "schedule":
        if len(sys.argv) < 3 or sys.argv[2] == "list":
            jobs = core.scheduler.list_jobs()
            print(f"\n{BOLD}Active Scheduled Directives ({len(jobs)}):{RESET}")
            for j in jobs:
                print(f"  ID: {j['id']:<14} Name: {j['name']:<30} Status: {CYAN}{j['status']}{RESET}")
        elif sys.argv[2] == "remove":
            if len(sys.argv) < 4:
                print("Usage: python main.py schedule remove <job_id>")
                return
            job_id = sys.argv[3]
            if core.scheduler.remove_job(job_id):
                print(f"{GREEN}[SUCCESS]{RESET} Job '{job_id}' erased from registry.")
            else:
                print(f"{RED}[ERROR]{RESET} Job '{job_id}' not found.")
        elif sys.argv[2] == "add":
            if len(sys.argv) < 5:
                print("Usage: python main.py schedule add <name> <action: health_check|clean_temp|organize_downloads|backup> [interval_seconds]")
                return
            name = sys.argv[3]
            act = sys.argv[4]
            interval = int(sys.argv[5]) if len(sys.argv) > 5 else 3600
            job = core.scheduler.add_job(name=name, action=act, interval_seconds=interval)
            print(f"{GREEN}[SUCCESS]{RESET} Scheduled directive created: ID {job['id']} (Every {interval}s)")

    else:
        print_help()

if __name__ == "__main__":
    main()
