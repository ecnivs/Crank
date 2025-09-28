from google.genai import types
import wave
import os
import random
import logging

class TextToSpeech:
    def __init__(self, client, workspace):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = client
        self.workspace = workspace
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

    def save_to_wav(self, pcm):
        path = os.path.join(self.workspace, 'speech.wav')
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(30000)
            wf.writeframes(pcm)
        return path

    def get_audio(self, transcript):
        try:
            if not transcript:
                raise ValueError("Transcript must be a non-empty string")

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

            if not response.candidates:
                raise ValueError("No candidates returned from TTS model")
            if not response.candidates[0].content.parts:
                raise ValueError("No content parts returned in response")

            data = response.candidates[0].content.parts[0].inline_data.data
            if not data:
                raise ValueError("No audio data found in response")

            path = self.save_to_wav(data)
            self.logger.info(f"Audio saved to {path}")
            return path

        except Exception as e:
            raise RuntimeError(f"Failed to generate audio") from e
