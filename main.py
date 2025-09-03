import datetime
from googleapiclient.http import ResumableUploadError
from google import genai
from caption_handler import CaptionHandler
from response_handler import ResponseHandler
from config_handler import ConfigHandler
from youtube_handler import YoutubeHandler
from media_handler import MediaHandler
from video_editor import VideoEditor
from contextlib import contextmanager
import asyncio
import logging
import os
import shutil
import tempfile
from dotenv import load_dotenv
from pathlib import Path
from argparse import ArgumentParser

load_dotenv()

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s - %(message)s',
                    force=True)

# -------------------------------
# Temporary Workspace
# -------------------------------
@contextmanager
def new_workspace():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)

class Core:
    def __init__(self, workspace, path):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = ConfigHandler(path)
        self.client = genai.Client(api_key = (self.config.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")))
        self.workspace = Path(workspace)
        self.media_handler = MediaHandler(workspace = self.workspace)
        self.video_editor = VideoEditor()
        self.caption_handler = CaptionHandler(workspace = self.workspace, model_size = "tiny")
        self.response_handler = ResponseHandler(client = self.client, workspace = self.workspace)

        if self.config.get("UPLOAD") is not False:
            self.youtube_handler = YoutubeHandler(self.config.get("NAME"))

    def _time_left(self, num_hours):
        limit_time = self.config.get("LIMIT_TIME")
        if not limit_time:
            return 0
        limit_time_dt = datetime.datetime.fromisoformat(limit_time)
        elapsed = datetime.datetime.now(datetime.UTC) - limit_time_dt
        hours = datetime.timedelta(hours = num_hours)
        return int(max((hours - elapsed).total_seconds(), 0))

    def _upload(self, content, output_path):
        title = self.response_handler.gemini(f"{self.config.get('GET_TITLE')}\n\n{content}", model = 1.5)
        description = self.config.get("DESCRIPTION")
        try:
            self.config.set("LAST_UPLOAD", self.youtube_handler.upload(
                video_path = output_path,
                title = title,
                tags = self.config.get("TAGS") or [],
                description = description,
                categoryId = self.config.get("CATEGORY_ID", default = 24),
                delay = self.config.get("DELAY", 0),
                last_upload = self.config.get("LAST_UPLOAD") or datetime.datetime.now(datetime.UTC)
            ))
        except ResumableUploadError:
            self.config.set("LIMIT_TIME", str(datetime.datetime.now(datetime.UTC).isoformat()))
        current = self.config.get("USED_CONTENT") or []
        if title not in current:
            current.append(title.strip())
            self.config.set("USED_CONTENT", current[-100:])

    async def run(self):
        try:
            while True:
                if hasattr(self, "youtube_handler"):
                    time_left = self._time_left(num_hours = 24)
                    while time_left > 0:
                        hours, minutes, seconds = time_left // 3600, (time_left % 3600) // 60, time_left % 60
                        print(f"\r[{self.config.get("NAME")}] Crank will continue in {hours}h {minutes}m {seconds}s", end="")
                        await asyncio.sleep(1)
                        time_left -= 1

                content = self.response_handler.gemini(query = f"{self.config.get('CONTENT_PROMPT')}\n\nAvoid ALL topics related to: {self.config.get('USED_CONTENT') or []}\n\n Return ONLY fresh content.", model = 2.0)
                media_path = self.media_handler.process(self.response_handler.gemini(f"{self.config.get('TERM_PROMPT')}\n{content}", model=2.5))
                audio_path = self.response_handler.get_audio(transcript = content)
                ass_path = self.caption_handler.get_captions(audio_path = audio_path)
                output_path = self.video_editor.process_video(ass_path = ass_path, audio_path = audio_path, media_path = media_path)

                if not hasattr(self, "youtube_handler"):
                    break
                self._upload(content = content, output_path = output_path)
        except RuntimeError as e:
            self.logger.critical(e)
        except KeyboardInterrupt as e:
            self.logger.info(f"Shutting down...")
        except Exception as e:
            self.logger.error(e)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--path", help = "Path to config.yml", default = "config.yml")
    args = parser.parse_args()
    path = args.path

    with new_workspace() as workspace:
        core = Core(workspace, path)
        asyncio.run(core.run())
