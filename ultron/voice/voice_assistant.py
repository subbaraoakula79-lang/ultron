from typing import Any, Callable, Dict, Optional
from ultron.voice.speech_recognition import SpeechRecognizer
from ultron.voice.speech_synthesis import SpeechSynthesizer


class VoiceAssistant:
    """Orchestrates wake-word detection, live spoken responses, and audio hardware."""

    def __init__(self, wake_word: str = "ultron"):
        self.wake_word = wake_word.lower()
        self.synthesizer = SpeechSynthesizer()
        self.recognizer = SpeechRecognizer()

    def speak(self, text: str, async_mode: bool = True):
        self.synthesizer.speak(text, async_mode=async_mode)

    def stop_speaking(self):
        self.synthesizer.stop()

    def check_wake_word(self, phrase: str) -> bool:
        return self.wake_word in phrase.lower()

    def get_hardware_status(self) -> Dict[str, Any]:
        mic = self.recognizer.check_microphone_availability()
        return {
            "tts_available": True,
            "microphone": mic,
            "wake_word": self.wake_word
        }
