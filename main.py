import datetime
from settings import *
from google import genai
from speech_handler import SpeechHandler
from caption_handler import CaptionHandler
from response_handler import ResponseHandler
from state_handler import StateHandler
from youtube_handler import YoutubeHandler
from media_handler import MediaHandler
from video_editor import VideoEditor
import asyncio
import os
import time

class Core:
    def __init__(self, workspace):
        self.client = genai.Client(api_key = os.environ['GEMINI_API_KEY2'])
        self.workspace = workspace
        self.state = StateHandler()
        self.media_handler = MediaHandler(workspace = self.workspace)
        self.video_editor = VideoEditor(workspace = self.workspace)
        self.youtube_handler = YoutubeHandler()
        self.caption_handler = CaptionHandler(workspace = self.workspace, model_size = "tiny")
        self.speech_handler = SpeechHandler(client = self.client, workspace = self.workspace)
        self.response_handler = ResponseHandler(client = self.client)

    def _time_left(self, num_hours):
        limit_time = self.state.get("limit_time")
        if not limit_time:
            return 0
        limit_time_dt = datetime.datetime.fromisoformat(limit_time)
        elapsed = datetime.datetime.now(datetime.UTC) - limit_time_dt
        hours = datetime.timedelta(hours = num_hours)
        return int(max((hours - elapsed).total_seconds(), 0))

    async def run(self):
        try:
            while True:
                content = self.response_handler.gemini(query = CONTENT_PROMPT, model = 2.0)
                media_path = self.media_handler.process(self.response_handler.gemini(f"{TERM_PROMPT}\n{content}", model=2.5))
                audio_path = self.speech_handler.get_audio(transcript = content)
                ass_path = self.caption_handler.get_captions(audio_path = audio_path)
                output_path = self.video_editor.process_video(ass_path = ass_path, audio_path = audio_path, media_path = media_path)

                logging.info(output_path)
                await asyncio.sleep(1000)

                time_left = self._time_left(num_hours = 24)
                if time_left:
                    logging.info(f"[{self.__class__.__name__}] Crank will continue in {time_left} secs")
                    await asyncio.sleep(time_left)

        except RuntimeError as e:
            logging.critical(e)
        except KeyboardInterrupt as e:
            logging.info(f"[{self.__class__.__name__}] Shutting down...")
        except Exception as e:
            logging.error(e)

if __name__ == "__main__":
    with new_workspace() as workspace:
        core = Core(workspace)
        asyncio.run(core.run())
