import os
import subprocess
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional

COMMON_ADB_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "platform-tools" / "adb.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Android" / "platform-tools" / "adb.exe",
]

class PhoneController:
    """Automates physical Android devices & emulators via ADB & Google ARTEMIS."""
    def __init__(self, adb_path: Optional[str] = None):
        self.adb_bin = self._resolve_adb(adb_path)

    def _resolve_adb(self, custom_path: Optional[str] = None) -> Optional[str]:
        if custom_path and Path(custom_path).exists():
            return str(Path(custom_path).resolve())

        for p in COMMON_ADB_PATHS:
            if p.exists():
                return str(p)

        # Check system PATH
        try:
            res = subprocess.run(["where", "adb"], capture_output=True, text=True)
            if res.returncode == 0:
                first_line = res.stdout.strip().split("\n")[0].strip()
                if Path(first_line).exists():
                    return first_line
        except Exception:
            pass

        return None

    def _run_adb(self, args: List[str], timeout: int = 15) -> Dict[str, Any]:
        if not self.adb_bin:
            return {"success": False, "error": "ADB binary not found on system."}

        cmd = [self.adb_bin] + args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "exit_code": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"ADB command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_devices(self) -> List[Dict[str, str]]:
        """Returns list of connected Android devices/emulators."""
        res = self._run_adb(["devices"])
        if not res.get("success"):
            return []
        devices = []
        for line in res.get("stdout", "").split("\n")[1:]:
            parts = line.strip().split()
            if len(parts) >= 2:
                devices.append({"serial": parts[0], "status": parts[1]})
        return devices

    def get_phone_status(self) -> Dict[str, Any]:
        """Collects device battery, screen state, and OS version."""
        devices = self.get_devices()
        if not devices:
            return {
                "connected": False,
                "message": "No Android device connected. Connect via USB or Wi-Fi (adb connect <ip>:5555)."
            }

        target = devices[0]["serial"]
        
        # Battery
        battery_res = self._run_adb(["-s", target, "shell", "dumpsys", "battery"])
        battery_level = "Unknown"
        if battery_res.get("success"):
            for line in battery_res["stdout"].split("\n"):
                if "level:" in line:
                    battery_level = line.split(":")[-1].strip() + "%"
                    break

        # Model & Android Version
        model_res = self._run_adb(["-s", target, "shell", "getprop", "ro.product.model"])
        version_res = self._run_adb(["-s", target, "shell", "getprop", "ro.build.version.release"])

        return {
            "connected": True,
            "device_serial": target,
            "model": model_res.get("stdout", "Android Device"),
            "android_version": version_res.get("stdout", "Unknown"),
            "battery": battery_level,
            "total_connected_devices": len(devices)
        }

    def open_app(self, app_name: str) -> Dict[str, Any]:
        """Launches common apps by name or package on phone."""
        app_map = {
            "whatsapp": "com.whatsapp",
            "chrome": "com.android.chrome",
            "browser": "com.android.chrome",
            "youtube": "com.google.android.youtube",
            "maps": "com.google.android.apps.maps",
            "messages": "com.google.android.apps.messaging",
            "sms": "com.google.android.apps.messaging",
            "settings": "com.android.settings",
            "camera": "com.android.camera",
            "bookmyshow": "com.bt.bms",
            "makemytrip": "com.makemytrip",
            "irctc": "cris.org.in.prs.ima",
            "uber": "com.ubercab",
            "spotify": "com.spotify.music"
        }

        package = app_map.get(app_name.lower().strip(), app_name.strip())
        res = self._run_adb(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
        if res.get("success"):
            return {"success": True, "message": f"Launched '{app_name}' ({package}) on phone."}
        else:
            return {"success": False, "error": f"Failed to launch app: {res.get('stderr') or res.get('error')}"}

    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Opens messaging app and pre-fills SMS on phone."""
        clean_phone = phone_number.replace(" ", "").replace("-", "")
        # Launch SMS intent
        intent_args = [
            "shell", "am", "start",
            "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{clean_phone}",
            "--es", "sms_body", message
        ]
        res = self._run_adb(intent_args)
        if res.get("success"):
            return {
                "success": True,
                "message": f"SMS draft prepared for {clean_phone} with text: \"{message}\". Screen active on device.",
                "recipient": clean_phone
            }
        return {"success": False, "error": res.get("stderr") or res.get("error")}

    def send_whatsapp(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Opens WhatsApp on phone with pre-filled message ready to send."""
        clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

        intent_args = [
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", wa_url,
            "com.whatsapp"
        ]
        res = self._run_adb(intent_args)
        if res.get("success"):
            return {
                "success": True,
                "message": f"WhatsApp opened on phone directed to {phone_number} with message staged.",
                "whatsapp_url": wa_url
            }
        return {"success": False, "error": res.get("stderr") or res.get("error")}

    def search_on_phone(self, query: str) -> Dict[str, Any]:
        """Executes a web search on the mobile device."""
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        intent_args = [
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", search_url
        ]
        res = self._run_adb(intent_args)
        if res.get("success"):
            return {"success": True, "message": f"Executed mobile web search for: '{query}' on device."}
        return {"success": False, "error": res.get("stderr") or res.get("error")}

    def take_screenshot(self, save_path: str = "phone_screenshot.png") -> Dict[str, Any]:
        """Captures mobile screen and pulls it to the local machine."""
        temp_device_path = "/sdcard/ultron_screen.png"
        res1 = self._run_adb(["shell", "screencap", "-p", temp_device_path])
        if not res1.get("success"):
            return {"success": False, "error": f"Failed to capture screen: {res1.get('error')}"}

        res2 = self._run_adb(["pull", temp_device_path, save_path])
        self._run_adb(["shell", "rm", temp_device_path])
        
        if res2.get("success"):
            return {"success": True, "file": save_path, "message": f"Mobile screenshot saved to {save_path}"}
        return {"success": False, "error": "Failed to pull screenshot file from device."}

    def type_text(self, text: str) -> Dict[str, Any]:
        """Types text on phone via ADB keyboard."""
        safe_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        return self._run_adb(["shell", "input", "text", safe_text])

    def press_key(self, key_code: int) -> Dict[str, Any]:
        """Presses an Android key (e.g. 3=Home, 4=Back, 66=Enter, 26=Power)."""
        return self._run_adb(["shell", "input", "keyevent", str(key_code)])
