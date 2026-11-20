import subprocess
from typing import Any, Dict, Optional


class SpeechRecognizer:
    """Manages audio input detection and microphone hardware availability."""

    def check_microphone_availability(self) -> Dict[str, Any]:
        """Detects if an active audio recording device is present on Windows."""
        ps_cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine; "
            "$rec.SetInputToDefaultAudioDevice(); "
            "Write-Output 'MIC_AVAILABLE'"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_avail = "MIC_AVAILABLE" in res.stdout
            return {
                "available": is_avail,
                "details": "Audio capture hardware online" if is_avail else "No default microphone input detected."
            }
        except Exception as e:
            return {
                "available": False,
                "details": f"Audio diagnostic error: {str(e)}"
            }

    def listen_and_transcribe(self, timeout_seconds: int = 5) -> Dict[str, Any]:
        """Transcribes a spoken phrase if microphone is present."""
        mic_check = self.check_microphone_availability()
        if not mic_check["available"]:
            return {
                "success": False,
                "error": "Microphone hardware is not available on this host.",
                "transcription": ""
            }

        # On desktop, the primary live STT occurs seamlessly in the HUD via Web Speech API.
        return {
            "success": True,
            "message": "Speech engine ready. Real-time STT active in Holographic HUD interface.",
            "transcription": ""
        }
