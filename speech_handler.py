from google.genai import types
import wave
import os
import random
import logging

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s - %(message)s',
                    force=True)

class SpeechHandler:
    def __init__(self, client, workspace):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = client
        self.workspace = workspace
        self.voices = [
            'Zephyr', 'Kore', 'Orus', 'Autonoe', 'Umbriel',
            'Erinome', 'Laomedeia', 'Schedar', 'Achird', 'Sadachbia',
            'Puck', 'Fenrir', 'Aoede', 'Enceladus', 'Algieba',
            'Algenib', 'Achernar', 'Gacrux', 'Zubenelgenubi', 'Sadaltager',
            'Charon', 'Leda', 'Callirrhoe', 'Iapetus', 'Despina',
            'Rasalgethi', 'Alnilam', 'Pulcherrima', 'Vindemiatrix', 'Sulafat'
        ]

    def save_to_wav(self, pcm):
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
                            voice_name=random.choice(random.choice(self.voices)),
                        )
                    )
                ),
            )
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        path = self.save_to_wav(data)
        self.logger.info(f"Audio saved to {path}")
        return path
