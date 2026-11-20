import pytest
from ultron.voice.voice_assistant import VoiceAssistant
from ultron.voice.speech_synthesis import SpeechSynthesizer
from ultron.voice.speech_recognition import SpeechRecognizer


def test_voice_assistant_wake_word():
    va = VoiceAssistant(wake_word="ultron")
    assert va.check_wake_word("Ultron, check system health") is True
    assert va.check_wake_word("Open notepad") is False


def test_speech_recognizer_interface():
    rec = SpeechRecognizer()
    status = rec.check_microphone_availability()
    assert "available" in status
    assert "details" in status


def test_speech_synthesis_sanitization():
    synth = SpeechSynthesizer()
    # Ensure stop does not throw when idle
    synth.stop()
    assert synth._current_process is None
