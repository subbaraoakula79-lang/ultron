import sys
import subprocess
from typing import Optional

class VoiceEngine:
    """Windows native SAPI Speech Synthesis & Voice Command helper."""
    def __init__(self, voice_name: Optional[str] = None, rate: int = -1, volume: int = 100):
        self.rate = rate  # -10 to 10 (-1 is slightly slower, deeper, calculating)
        self.volume = volume # 0 to 100
        self.voice_name = voice_name

    def speak(self, text: str, async_mode: bool = True):
        """Speaks the text using Windows SAPI SpeechSynthesizer."""
        if sys.platform != "win32":
            return
        
        # Sanitize text for PowerShell
        clean_text = text.replace('"', '`"').replace("'", "''").replace("\n", " ")
        ps_script = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = {self.rate}; "
            f"$synth.Volume = {self.volume}; "
            f"$synth.Speak(\"{clean_text}\");"
        )
        try:
            if async_mode:
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
        except Exception as e:
            print(f"[!] Voice synthesis warning: {e}")
