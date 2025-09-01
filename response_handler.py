import logging
from google.genai import types
import os
import random
import logging
import wave

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s - %(message)s',
                    force=True)

class ResponseHandler:
    def __init__(self, client, workspace):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = client
        self.workspace = workspace
        self.models = {
            "2.5": "gemini-2.5-flash",
            "2.0": "gemini-2.0-flash",
            "1.5": "gemini-1.5-flash",
        }
        self.voices = [
            'Zephyr',
            'Kore',
            'Orus',
            'Autonoe',
            'Umbriel',
            'Erinome',
            'Laomedeia',
            'Schedar',
            'Achird',
            'Sadachbia',
            'Puck',
            'Fenrir',
            'Aoede',
            'Enceladus',
            'Algieba',
            'Algenib',
            'Achernar',
            'Gacrux',
            'Zubenelgenubi',
            'Sadaltager',
            'Charon',
            'Leda',
            'Callirrhoe',
            'Iapetus',
            'Despina',
            'Rasalgethi',
            'Alnilam',
            'Pulcherrima',
            'Vindemiatrix',
            'Sulafat'
        ]

    def _save_to_wav(self, pcm):
        path = os.path.join(self.workspace, 'speech.wav')
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(30000)
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
                            voice_name=random.choice(self.voices),
                        )
                    )
                ),
            )
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        path = self._save_to_wav(data)
        self.logger.info(f"Audio saved to {path}")
        return path

    def gemini(self, query, model):
        current_model = self.models.get(str(model))
        response = self.client.models.generate_content(
            model = current_model,
            contents = query
        )
        self.logger.info(f"Gemini returned: {response.text}")
        return response.text
