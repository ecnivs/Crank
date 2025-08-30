from google.genai import types
from settings import *
import wave
import os
import random

# TODO: Increase speaking rate

class SpeechHandler:
    def __init__(self, client, workspace):
        self.client = client
        self.workspace = workspace

    def save_to_wav(self, pcm, channels=1, rate=24000, sample_width=2):
        path = os.path.join(self.workspace, 'speech.wav')
        with wave.open(path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)
        return path

    def get_audio(self, transcript):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=transcript,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=random.choice(VOICES),
                        )
                    )
                ),
            )
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        path = self.save_to_wav(data)
        logging.info(f"[{self.__class__.__name__}] Audio saved to {path}")
        return path
