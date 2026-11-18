import os
import json
import webbrowser
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

from ultron.core import UltronCore

HUD_DIR = Path(__file__).parent / "hud"
mimetypes.add_type("application/vnd.android.package-archive", ".apk")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class UltronHudHandler(SimpleHTTPRequestHandler):
    core: UltronCore = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HUD_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self._handle_api_status()
        elif self.path == "/api/tasks":
            self._handle_api_tasks()
        else:
            # Serve static files from HUD_DIR
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/command":
            self._handle_api_command()
        else:
            self.send_error(404, "Endpoint Not Found")

    def _handle_api_status(self):
        metrics = self.core.monitor.get_metrics()
        active_provider = self.core.provider_mgr.get_active_provider()
        engine_name = "GLM-4-Flash" if active_provider and "GLM" in str(getattr(active_provider, "provider", "")) else (getattr(active_provider, "model", "Heuristic") if active_provider else "Heuristic Core")
        metrics["engine"] = engine_name
        self._send_json(metrics)

    def _handle_api_tasks(self):
        tasks = self.core.scheduler.list_jobs()
        self._send_json({"tasks": tasks})

    def _handle_api_command(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        try:
            req_data = json.loads(post_body.decode("utf-8"))
            cmd_text = req_data.get("command", "")
            response_text = self.core.process_instruction(cmd_text)
            
            # Speak directly through PC speakers via Windows SAPI hardware
            first_sentence = response_text.split("\n")[0].strip(' "[]')
            if first_sentence:
                self.core.voice.speak(first_sentence, async_mode=True)

            self._send_json({"success": True, "response": response_text})
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, status=500)

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silence routine static asset HTTP GET requests in terminal
        pass

def start_hud_server(port: int = 8080, open_browser: bool = True):
    core = UltronCore()
    UltronHudHandler.core = core
    
    # Try finding an open port starting from port
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
    core.notifier.success(f"Holographic Interface active at: {url}")
    core.notifier.info("Voice Command Synthesis & Recognition uplink established.")
    core.notifier.info("Press Ctrl+C to terminate the holographic HUD.")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        core.notifier.warning("Holographic Interface severed.")
        server.shutdown()
