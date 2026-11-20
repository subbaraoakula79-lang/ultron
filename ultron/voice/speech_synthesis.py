import os
import subprocess
import threading
from typing import Optional


class SpeechSynthesizer:
    """Windows SAPI speech synthesizer with asynchronous playback and interruptibility."""

    def __init__(self, rate: int = 0, volume: int = 100):
        self.rate = rate
        self.volume = volume
        self._current_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def speak(self, text: str, async_mode: bool = True):
        """Synthesizes text through local audio hardware."""
        if not text or not text.strip():
            return

        # Sanitize text for PowerShell string
        clean_text = text.replace("'", "''").replace('"', '""').replace("\n", " ").strip()

        ps_script = (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = {self.rate}; "
            f"$synth.Volume = {self.volume}; "
            f"$synth.Speak('{clean_text}');"
        )

        def _run():
            with self._lock:
                self.stop()
                try:
                    self._current_process = subprocess.Popen(
                        ["powershell", "-NoProfile", "-Command", ps_script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception:
                    self._current_process = None

            if not async_mode and self._current_process:
                self._current_process.wait()

        if async_mode:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
        else:
            _run()

    def stop(self):
        """Interrupts any currently playing speech synthesis."""
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                except Exception:
                    pass
                self._current_process = None
