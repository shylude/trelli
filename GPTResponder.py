from openai import OpenAI
from keys import OPENAI_API_KEY
from prompts import create_prompt, INITIAL_RESPONSE
import time

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4o-mini"
MAX_TOKENS = 160


def generate_response_from_transcript(transcript: str) -> str:
    if not transcript.strip():
        return ""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": create_prompt(transcript)}
            ],
            temperature=0.0,
            max_tokens=MAX_TOKENS,
        )

        content = resp.choices[0].message.content or ""

        # If brackets exist, extract them
        if "[" in content and "]" in content:
            return content.split("[", 1)[1].split("]", 1)[0].strip()

        # Otherwise return raw content
        return content.strip()

    except Exception as e:
        return f"OpenAI error: {str(e)}"


class GPTResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 1.0
        self._last_transcript = ""

    def respond_to_transcriber(self, transcriber):
        while True:
            if not transcriber.transcript_changed_event.is_set():
                time.sleep(0.15)
                continue

            transcriber.transcript_changed_event.clear()
            transcript = transcriber.get_transcript()

            if transcript == self._last_transcript:
                time.sleep(0.15)
                continue

            self._last_transcript = transcript
            response = generate_response_from_transcript(transcript)

            if response:
                self.response = response

            time.sleep(self.response_interval)

    def update_response_interval(self, interval):
        try:
            self.response_interval = max(0.3, float(interval))
        except Exception:
            self.response_interval = 1.0
