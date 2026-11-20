import json
import mimetypes
import os
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Dict, Optional

from ultron.config import Config
from ultron.ai.model_manager import ModelManager
from ultron.agent.permission_manager import PermissionManager
from ultron.agent.tool_registry import ToolRegistry
from ultron.agent.agent import UltronAgent
from ultron.tools.desktop.desktop_controller import DesktopController
from ultron.integrations.artemis.device_manager import DeviceManager
from ultron.integrations.artemis.artemis_client import ArtemisClient
from ultron.integrations.artemis.android_tasks import AndroidTaskRunner
from ultron.memory.memory_manager import MemoryManager
from ultron.voice.voice_assistant import VoiceAssistant
from ultron.tools.scheduler import TaskScheduler

HUD_DIR = (Path(__file__).parent / "hud").resolve()
mimetypes.add_type("application/vnd.android.package-archive", ".apk")
MAX_REQUEST_BODY_BYTES = 1024 * 1024  # 1 MB maximum payload


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class UltronHudHandler(SimpleHTTPRequestHandler):
    agent: UltronAgent = None
    model_mgr: ModelManager = None
    desktop: DesktopController = None
    device_mgr: DeviceManager = None
    artemis: ArtemisClient = None
    memory: MemoryManager = None
    voice: VoiceAssistant = None
    scheduler: TaskScheduler = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HUD_DIR), **kwargs)

    def _is_origin_allowed(self) -> bool:
        """Restricts CORS to localhost origins."""
        origin = self.headers.get("Origin", "")
        if not origin:
            return True
        parsed = urllib.parse.urlparse(origin)
        return parsed.hostname in ["127.0.0.1", "localhost"]

    def do_OPTIONS(self):
        """Handles CORS preflight requests securely."""
        if self._is_origin_allowed():
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", "http://127.0.0.1:8080"))
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        else:
            self.send_error(403, "Origin Forbidden")

    def do_GET(self):
        if self.path == "/api/status":
            self._handle_api_status()
        elif self.path == "/api/tasks":
            self._handle_api_tasks()
        elif self.path == "/api/memory":
            self._handle_api_memory()
        else:
            # Prevent directory traversal attacks
            requested_path = (HUD_DIR / self.path.lstrip("/")).resolve()
            if not str(requested_path).startswith(str(HUD_DIR)):
                self.send_error(403, "Access Denied")
                return
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/command":
            self._handle_api_command()
        elif self.path == "/api/confirm":
            self._handle_api_confirm()
        else:
            self.send_error(404, "Endpoint Not Found")

    def _handle_api_status(self):
        sys_status = self.desktop.get_system_status()
        ai_status = self.model_mgr.get_status_report()
        dev_status = self.device_mgr.get_device_status()
        artemis_status = self.artemis.get_status()

        payload = {
            "online": True,
            "engine": ai_status.get("effective_model", "Qwen 2B (Local)"),
            "ai_status": ai_status,
            "system": sys_status,
            "device": dev_status,
            "artemis": artemis_status,
            "audit_trail": self.agent.permissions.get_audit_trail()[-10:]
        }
        self._send_json(payload)

    def _handle_api_tasks(self):
        tasks = self.scheduler.list_jobs() if self.scheduler else []
        self._send_json({"tasks": tasks})

    def _handle_api_memory(self):
        facts = self.memory.long_term.list_all_facts() if self.memory else []
        self._send_json({"facts": facts})

    def _handle_api_command(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > MAX_REQUEST_BODY_BYTES:
            self.send_error(413, "Payload Too Large (Max 1MB)")
            return

        body = self.rfile.read(content_len)
        try:
            req = json.loads(body.decode("utf-8"))
            command_text = req.get("command", "").strip()
            if not command_text:
                self._send_json({"success": False, "error": "Empty command"}, status=400)
                return

            response_text = self.agent.process(command_text)

            # Speak first sentence asynchronously through local speakers
            first_sentence = response_text.split("\n")[0].strip(' "[]*#')
            if first_sentence and self.voice:
                self.voice.speak(first_sentence, async_mode=True)

            # Record turn in persistent SQLite database
            if self.memory:
                self.memory.record_turn("hud_session", command_text, response_text)

            self._send_json({
                "success": True,
                "response": response_text
            })
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, status=500)

    def _handle_api_confirm(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        try:
            req = json.loads(body.decode("utf-8"))
            token = req.get("token", "").strip()
            if not token:
                self._send_json({"success": False, "error": "Missing confirmation token"}, status=400)
                return

            response_text = self.agent.process(f"confirm {token}", confirmation_token=token)
            self._send_json({"success": True, "response": response_text})
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, status=500)

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if self._is_origin_allowed():
            origin = self.headers.get("Origin", "http://127.0.0.1:8080")
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silence routine static asset GET logs in terminal
        pass


def build_ultron_system(config_path: str = "config.json") -> Dict[str, Any]:
    """Assembles all Ultron subsystems into a cohesive agent engine."""
    config = Config(config_path)
    model_mgr = ModelManager(config.data)
    permission_mgr = PermissionManager()
    registry = ToolRegistry()

    desktop = DesktopController()
    device_mgr = DeviceManager()
    artemis = ArtemisClient()
    android_tasks = AndroidTaskRunner(device_mgr)
    memory = MemoryManager()
    voice = VoiceAssistant()
    scheduler = TaskScheduler(schedule_file=config.get("automation.schedules_file", "schedules.json"))

    # Register all core tools into the registry
    registry.register_tool(
        name="desktop_app",
        description="Launches an approved desktop application on the PC (e.g. calc, notepad, code, chrome).",
        parameters={
            "type": "object",
            "properties": {
                "app": {"type": "string", "description": "Application name: calc, notepad, code, chrome, edge"},
                "file": {"type": "string", "description": "Optional file path to open with the application"}
            },
            "required": ["app"]
        },
        handler=lambda app, file=None: desktop.open_application(app, target_file=file)
    )

    registry.register_tool(
        name="system_status",
        description="Retrieves live system telemetry: CPU percent, RAM available, disk usage.",
        parameters={"type": "object", "properties": {}},
        handler=desktop.get_system_status
    )

    registry.register_tool(
        name="phone_status",
        description="Checks battery, model, and connectivity of connected Android device.",
        parameters={"type": "object", "properties": {}},
        handler=device_mgr.get_device_status
    )

    registry.register_tool(
        name="artemis_status",
        description="Checks Google ARTEMIS installation and Android automation readiness.",
        parameters={"type": "object", "properties": {}},
        handler=artemis.get_status
    )

    agent = UltronAgent(
        model_manager=model_mgr,
        tool_registry=registry,
        permission_manager=permission_mgr
    )

    return {
        "config": config,
        "model_mgr": model_mgr,
        "permission_mgr": permission_mgr,
        "registry": registry,
        "agent": agent,
        "desktop": desktop,
        "device_mgr": device_mgr,
        "artemis": artemis,
        "android_tasks": android_tasks,
        "memory": memory,
        "voice": voice,
        "scheduler": scheduler
    }


def start_hud_server(port: int = 8080, open_browser: bool = False):
    """Binds and launches the hardened Ultron HUD server."""
    components = build_ultron_system()

    UltronHudHandler.agent = components["agent"]
    UltronHudHandler.model_mgr = components["model_mgr"]
    UltronHudHandler.desktop = components["desktop"]
    UltronHudHandler.device_mgr = components["device_mgr"]
    UltronHudHandler.artemis = components["artemis"]
    UltronHudHandler.memory = components["memory"]
    UltronHudHandler.voice = components["voice"]
    UltronHudHandler.scheduler = components["scheduler"]

    server_address = ("127.0.0.1", port)
    for p in range(port, port + 10):
        try:
            server = ThreadedHTTPServer(("127.0.0.1", p), UltronHudHandler)
            actual_port = p
            break
        except OSError:
            continue
    else:
        print(f"[!] Could not bind to ports {port}-{port+9}")
        return

    url = f"http://127.0.0.1:{actual_port}/"
    print(f"[+] ULTRON Holographic Interface active at: {url}")
    print("[+] Localhost Security Enforced. Cloud providers disabled.")
    print("[+] Press Ctrl+C to terminate the HUD server.")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] ULTRON HUD server shut down safely.")
        server.server_close()
