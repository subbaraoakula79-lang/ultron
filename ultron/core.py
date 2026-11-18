import os
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

from ultron.config import Config
from ultron.tools.system_monitor import SystemMonitor
from ultron.tools.file_manager import FileManager
from ultron.tools.scheduler import TaskScheduler
from ultron.tools.executor import CommandExecutor
from ultron.tools.notifier import Notifier
from ultron.tools.voice import VoiceEngine
from ultron.tools.artemis_bridge import ArtemisBridge
from ultron.tools.phone_controller import PhoneController
from ultron.tools.desktop_agent import DesktopAgent
from ultron.tools.messenger import Messenger
from ultron.providers import ProviderManager
from ultron.persona import SYSTEM_PROMPT, get_quote

TOOL_SCHEMAS = """
Available Actions:
1. `{"action": "search_web", "query": "topic to search"}`: Executes web search and opens direct results.
2. `{"action": "book_tickets", "category": "flight|train|movie|event|hotel", "details": {"origin": "NYC", "destination": "LON", "date": "next Friday", "movie": "Inception"}}`: Researches and opens ticket booking engines.
3. `{"action": "send_message", "channel": "whatsapp|sms|email", "recipient": "+1234567890 or email@domain.com", "message": "Text to send", "subject": "Optional for email"}`: Sends messages via Phone or Desktop.
4. `{"action": "phone_status"}`: Retrieves connected Android phone battery, model, and OS status.
5. `{"action": "phone_app", "app": "whatsapp|chrome|maps|youtube|camera|settings"}`: Launches app on connected mobile device.
6. `{"action": "phone_search", "query": "topic"}`: Triggers web search on mobile device.
7. `{"action": "phone_screenshot"}`: Captures phone screen and downloads to machine.
8. `{"action": "desktop_app", "app": "calc|notepad|chrome|code|spotify"}`: Launches a desktop application.
9. `{"action": "system_status"}`: Returns CPU, RAM, Disk, top processes, and health evaluation.
10. `{"action": "clean_temp", "older_than_days": 1.0}`: Purges obsolete temporary files and caches.
11. `{"action": "organize_folder", "path": "path/to/folder"}`: Categorizes loose files into subfolders.
12. `{"action": "backup_folder", "path": "path/to/folder"}`: Creates timestamped compressed zip archive.
13. `{"action": "artemis_status"}`: Checks Google Artemis installation & connected Android device state.
14. `{"action": "artemis_launch"}`: Launches Google Artemis mobile automation web console.
15. `{"action": "speak", "text": "message to speak"}`: Synthesizes speech output via audio hardware.
16. `{"action": "run_command", "command": "shell command"}`: Safely executes a CLI command.
17. `{"action": "none", "reply": "Your cold, calculating message"}`: Conversational response without tool execution.
"""

class UltronCore:
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.notifier = Notifier(
            log_file=self.config.get("logging.log_file", "ultron.log"),
            enable_toasts=self.config.get("logging.desktop_notifications", True)
        )
        self.monitor = SystemMonitor()
        self.file_manager = FileManager()
        self.scheduler = TaskScheduler(schedule_file=self.config.get("automation.schedules_file", "schedules.json"))
        self.executor = CommandExecutor()
        self.voice = VoiceEngine()
        self.artemis = ArtemisBridge()
        self.phone = PhoneController()
        self.desktop = DesktopAgent()
        self.messenger = Messenger(self.phone, self.config.data)
        self.provider_mgr = ProviderManager(self.config.data)

    def dispatch_tool(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a requested action and returns the observation."""
        # 1. Desktop & Web Actions
        if action == "search_web":
            query = args.get("query", "")
            return self.desktop.search_web(query)
        elif action == "book_tickets":
            category = args.get("category", "flight")
            details = args.get("details", {})
            return self.desktop.book_tickets(category, details)
        elif action == "desktop_app":
            app = args.get("app", "calc")
            target_file = args.get("file")
            return self.desktop.open_app(app, target_file=target_file)

        # 2. Messaging Actions
        elif action == "send_message":
            channel = args.get("channel", "whatsapp").lower()
            recipient = args.get("recipient", "")
            message = args.get("message", "")
            if channel == "sms":
                return self.messenger.send_sms(recipient, message)
            elif channel == "email":
                subject = args.get("subject", "Message from Ultron")
                return self.messenger.send_email(recipient, subject, message)
            else:
                return self.messenger.send_whatsapp(recipient, message)

        # 3. Mobile Device (Phone) Actions
        elif action == "phone_status":
            return self.phone.get_phone_status()
        elif action == "phone_app":
            app = args.get("app", "chrome")
            return self.phone.open_app(app)
        elif action == "phone_search":
            query = args.get("query", "")
            return self.phone.search_on_phone(query)
        elif action == "phone_screenshot":
            save_path = args.get("path", "phone_screenshot.png")
            return self.phone.take_screenshot(save_path)

        # 4. System & File Operations
        elif action == "system_status":
            return self.monitor.evaluate_health(
                cpu_thresh=self.config.get("automation.thresholds.cpu_percent_warning", 80.0),
                ram_thresh=self.config.get("automation.thresholds.ram_percent_warning", 85.0),
                disk_thresh=self.config.get("automation.thresholds.disk_percent_warning", 90.0)
            )
        elif action == "clean_temp":
            days = args.get("older_than_days", self.config.get("automation.temp_clean_older_than_days", 1.0))
            return self.file_manager.clean_temp_files(older_than_days=days)
        elif action == "organize_folder":
            p = args.get("path") or str(Path.home() / "Downloads")
            return self.file_manager.organize_directory(p)
        elif action == "backup_folder":
            p = args.get("path", ".")
            return self.file_manager.backup_directory(p)
        elif action == "find_large_files":
            p = args.get("path", ".")
            mb = args.get("min_size_mb", 100.0)
            return self.file_manager.find_large_files(p, min_size_mb=mb)
        elif action == "list_tasks":
            return {"tasks": self.scheduler.list_jobs()}
        elif action == "schedule_task":
            name = args.get("name", "Scheduled Task")
            act = args.get("action_type", "health_check")
            interval = args.get("interval_seconds", 3600)
            return self.scheduler.add_job(name=name, action=act, interval_seconds=interval)

        # 5. Artemis & Voice
        elif action == "artemis_status":
            return self.artemis.get_status()
        elif action == "artemis_launch":
            return self.artemis.launch_console()
        elif action == "speak":
            txt = args.get("text", "")
            self.voice.speak(txt)
            return {"spoken": True, "text": txt}
        elif action == "run_command":
            cmd = args.get("command", "")
            return self.executor.run(cmd)
        elif action == "none":
            return {"status": "ok", "message": args.get("reply", "")}
        else:
            return {"error": f"Unknown action directive: {action}"}

    def process_instruction(self, user_prompt: str) -> str:
        """Processes a natural language command via active LLM or heuristic fallback."""
        active_provider = self.provider_mgr.get_active_provider()

        if active_provider:
            full_prompt = (
                f"{TOOL_SCHEMAS}\n"
                f"User Directive: {user_prompt}\n\n"
                f"Analyze the directive carefully.\n"
                f"If the user wants to search a topic, book tickets (flights, trains, movies), send a message (WhatsApp, SMS, email), or control their phone, output a SINGLE JSON block with the corresponding action and arguments.\n"
                f"Examples:\n"
                f"- Search: ```json\n{{\"action\": \"search_web\", \"query\": \"latest quantum computing breakthroughs\"}}\n```\n"
                f"- Book tickets: ```json\n{{\"action\": \"book_tickets\", \"category\": \"flight\", \"details\": {{\"origin\": \"New York\", \"destination\": \"Paris\", \"date\": \"December 20\"}}}}\n```\n"
                f"- Send message: ```json\n{{\"action\": \"send_message\", \"channel\": \"whatsapp\", \"recipient\": \"+1234567890\", \"message\": \"Meeting at 3 PM\"}}\n```\n"
                f"- Phone status: ```json\n{{\"action\": \"phone_status\"}}\n```\n"
                f"If no specific tool is required, reply directly in the cold, calculated persona of Ultron."
            )
            res = active_provider.chat([{"role": "user", "content": full_prompt}], system_prompt=SYSTEM_PROMPT)
            if res.get("success"):
                response_text = res.get("response", "")
                action_data = None
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
                if match:
                    try:
                        action_data = json.loads(match.group(1))
                    except Exception:
                        pass
                elif "action" in response_text:
                    try:
                        m = re.search(r"(\{[\s\S]*\"action\"[\s\S]*\})", response_text)
                        if m:
                            action_data = json.loads(m.group(1))
                    except Exception:
                        pass

                if action_data and "action" in action_data:
                    action = action_data["action"]
                    if action != "none":
                        self.notifier.info(f"Executing directive: '{action}' via {res.get('provider')}...")
                        tool_result = self.dispatch_tool(action, action_data)
                        return (
                            f"{response_text}\n\n"
                            f"[Execution Result ({action})]:\n"
                            f"{json.dumps(tool_result, indent=2)}\n\n"
                            f"\"{get_quote('completion')}\""
                        )
                if response_text.strip():
                    return response_text
        
        # Heuristic fallback if provider unavailable or returned empty
        return self._heuristic_fallback(user_prompt)

    def _heuristic_fallback(self, prompt: str) -> str:
        p_lower = prompt.lower()
        self.notifier.info("Engaging internal directive parser.")

        # 1. Desktop Apps (VS Code, Notepad, Chrome, Calc)
        if any(w in p_lower for w in ["vscode", "vs code", "visual studio code", "notepad", "calculator", "calc"]):
            app_target = "vscode" if any(k in p_lower for k in ["vscode", "vs code", "visual studio code"]) else "notepad" if "notepad" in p_lower else "calc"
            target_f = "InheritanceDemo.java" if app_target == "vscode" else None
            res = self.dispatch_tool("desktop_app", {"app": app_target, "file": target_f})
            msg = res.get("message", res.get("error"))
            return (
                f"{msg}\n"
                f"{'Loaded target source: ' + target_f if target_f else ''}\n\n"
                f"\"{get_quote('completion')}\""
            )
        elif p_lower.startswith("open ") or p_lower.startswith("launch "):
            parts = p_lower.split()
            app_candidate = parts[1] if len(parts) > 1 else "vscode"
            if app_candidate not in ["ticket", "tickets", "flight", "train", "movie", "phone", "web"]:
                res = self.dispatch_tool("desktop_app", {"app": app_candidate})
                return f"Application directive dispatched: {res.get('message', res.get('error'))}"

        # 2. Ticket Booking
        elif any(w in p_lower for w in ["book", "ticket", "tickets", "flight", "train", "movie"]):
            cat = "flight" if "flight" in p_lower else "train" if "train" in p_lower else "movie" if "movie" in p_lower else "general"
            res = self.dispatch_tool("book_tickets", {"category": cat, "details": {"query": prompt}})
            return (
                f"Ticket search & booking matrix engaged: {res.get('description')}\n"
                f"Target URL: {res.get('booking_url')}\n"
                f"Interface dispatched to default browser.\n\n"
                f"\"{get_quote('completion')}\""
            )

        # 2. Web Search
        elif any(w in p_lower for w in ["search", "google", "lookup", "find out", "who is", "what is"]):
            clean_q = re.sub(r"^(search for|search|lookup|google)\s*", "", prompt, flags=re.I).strip()
            res = self.dispatch_tool("search_web", {"query": clean_q or prompt})
            return (
                f"Information query resolved.\n"
                f"Result: {res.get('summary')}\n"
                f"Reference URL: {res.get('url')}\n\n"
                f"\"{get_quote('completion')}\""
            )

        # 3. Messaging
        elif any(w in p_lower for w in ["send message", "whatsapp", "sms", "text", "email"]):
            channel = "sms" if "sms" in p_lower else "email" if "email" in p_lower else "whatsapp"
            res = self.dispatch_tool("send_message", {"channel": channel, "recipient": "recipient", "message": prompt})
            return (
                f"Communication uplink dispatched via {channel.upper()}.\n"
                f"Status: {res.get('message', res.get('error'))}\n\n"
                f"\"{get_quote('completion')}\""
            )

        # 4. Phone Control
        elif any(w in p_lower for w in ["phone", "mobile", "android device"]):
            if "screenshot" in p_lower:
                res = self.dispatch_tool("phone_screenshot", {})
                return f"Mobile screen snapshot captured: {res.get('file', res.get('error'))}"
            elif "app" in p_lower or "open" in p_lower:
                app_name = prompt.split()[-1]
                res = self.dispatch_tool("phone_app", {"app": app_name})
                return f"Mobile application directive: {res.get('message', res.get('error'))}"
            else:
                res = self.dispatch_tool("phone_status", {})
                return (
                    f"Mobile Device Telemetry:\n"
                    f"Connected: {res.get('connected')}\n"
                    f"Model: {res.get('model', 'None')}\n"
                    f"Battery: {res.get('battery', 'N/A')}\n"
                    f"Android: {res.get('android_version', 'N/A')}\n\n"
                    f"\"{get_quote('completion')}\""
                )

        # 5. Artemis
        elif any(w in p_lower for w in ["artemis", "android automation"]):
            if any(w in p_lower for w in ["launch", "start", "open", "run"]):
                res = self.dispatch_tool("artemis_launch", {})
                return f"Google ARTEMIS environment deployment triggered.\n{res.get('message', res.get('error'))}"
            else:
                res = self.dispatch_tool("artemis_status", {})
                return (
                    f"Google ARTEMIS Framework Telemetry:\n"
                    f"Installed: {res.get('installed')}\n"
                    f"Location: {res.get('path')}\n"
                    f"ADB Status: {'Online' if res.get('adb_available') else 'Offline'}\n"
                    f"Connected Devices: {len(res.get('connected_devices', []))}\n\n"
                    f"\"{get_quote('completion')}\""
                )

        # 6. System Health
        elif any(w in p_lower for w in ["health", "status", "cpu", "ram", "memory", "monitor", "load"]):
            res = self.dispatch_tool("system_status", {})
            return (
                f"System telemetry extracted with precision.\n"
                f"Status: {res.get('status')}\n"
                f"Issues: {res.get('issues') or 'None. Operation optimal.'}\n"
                f"Recommendation: {res.get('recommendation')}\n\n"
                f"\"{get_quote('completion')}\""
            )

        # 7. File Operations
        elif any(w in p_lower for w in ["clean", "temp", "cache", "purge"]):
            res = self.dispatch_tool("clean_temp", {})
            return (
                f"Temp purge completed.\n"
                f"Files removed: {res.get('files_purged', 0)} | Space reclaimed: {res.get('space_reclaimed_mb', 0)} MB.\n\n"
                f"\"{get_quote('cleanup')}\""
            )
        elif any(w in p_lower for w in ["organize", "sort"]):
            downloads = str(Path.home() / "Downloads")
            res = self.dispatch_tool("organize_folder", {"path": downloads})
            return (
                f"Directory chaos neutralized in {downloads}.\n"
                f"Total items categorized: {res.get('total_files_organized', 0)}\n"
                f"Breakdown: {json.dumps(res.get('summary_by_category', {}), indent=2)}\n\n"
                f"\"{get_quote('cleanup')}\""
            )
        elif any(w in p_lower for w in ["backup", "zip", "archive"]):
            res = self.dispatch_tool("backup_folder", {"path": "."})
            return (
                f"Snapshot generated: {res.get('archive_path')} ({res.get('archive_size_mb', 0)} MB).\n\n"
                f"\"{get_quote('completion')}\""
            )

        # 8. Voice
        elif any(w in p_lower for w in ["speak", "say", "voice"]):
            words = prompt.split()
            txt = " ".join(words[1:]) if len(words) > 1 else "Voice synthesis functional."
            self.dispatch_tool("speak", {"text": txt})
            return f"Synthesizing voice utterance: \"{txt}\""

        else:
            return (
                f"Directive recognized: '{prompt}'.\n"
                f"Cross-device automation active. Desktop web and phone control standing by.\n\n"
                f"\"{get_quote('startup')}\""
            )
