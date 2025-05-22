from settings import *
from TTS.api import TTS
import torch

class SpeechHandler:
    def __init__(self, tts):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tts = tts.to(self.device)
        self.text_list = []
        self._ensure_frames_folder()

    @classmethod
    async def create(cls):
        tts = await asyncio.to_thread(TTS, model_name=TTS_MODEL, progress_bar=False)
        return cls(tts)

    def _ensure_frames_folder(self):
        os.makedirs(FRAMES_DIR, exist_ok=True)

    def _clear_frames(self):
        wav_files = glob.glob(os.path.join(FRAMES_DIR, '*.wav'))
        for file in wav_files:
            try:
                os.remove(file)
            except Exception as e:
                logging.error(f"Error removing {file}: {e}")

    def _get_audio_duration(self, file_path):
        try:
            audio = AudioSegment.from_wav(file_path)
            return len(audio) / 1000.0
        except Exception as e:
            logging.error(f"Error reading audio file {file_path}: {e}")
            return 0

    def add_text(self, text):
        if not isinstance(text, str) or not text.strip():
            logging.warning("Attempted to queue invalid text input.")
            return
        self.text_list.append(text)

    async def speak(self, speaker, clear=True):
        if clear:
            await asyncio.to_thread(self._clear_frames)

        timeline = [0.0]
        current_time = 0.0
        count = 1
        try:
            for item in self.text_list:
                output_wav = os.path.join(FRAMES_DIR, f"frame_{count}.wav")
                await asyncio.to_thread(
                    self.tts.tts_to_file,
                    item,
                    file_path=output_wav,
                    speaker_wav=speaker,
                    language='en'
                )
                audio_duration = await asyncio.to_thread(self._get_audio_duration, output_wav)
                current_time += audio_duration
                timeline.append(current_time)
                count += 1
                await asyncio.sleep(0.05)

            self.text_list = []
            return timeline
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] TTS processing failed") from e
