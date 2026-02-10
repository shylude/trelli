from openai import OpenAI
from keys import OPENAI_API_KEY
import whisper
import os
import torch

client = OpenAI(api_key=OPENAI_API_KEY)

def get_model(use_api):
    if use_api:
        return APIWhisperTranscriber()
    else:
        return WhisperTranscriber()

def _get_text(obj):
    """
    Handles:
    - dict responses: {"text": "..."}
    - objects with .text
    - objects with .get("text")
    """
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return (obj.get("text") or "").strip()
    # some SDK objects support dict-like get
    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return (getter("text") or "").strip()
        except Exception:
            pass
    return (getattr(obj, "text", "") or "").strip()

class WhisperTranscriber:
    def __init__(self):
        self.audio_model = whisper.load_model(os.path.join(os.getcwd(), "tiny.en.pt"))
        print(f"[INFO] Whisper using GPU: {torch.cuda.is_available()}")

    def get_transcription(self, wav_file_path):
        try:
            result = self.audio_model.transcribe(wav_file_path, fp16=torch.cuda.is_available())
        except Exception as e:
            print(e)
            return ""
        # openai-whisper returns a dict with "text"
        return _get_text(result)

class APIWhisperTranscriber:
    def get_transcription(self, wav_file_path):
        try:
            with open(wav_file_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
        except Exception as e:
            print(e)
            return ""
        return _get_text(result)