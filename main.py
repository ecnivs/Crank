import datetime
from googleapiclient.http import ResumableUploadError
from google import genai
from caption import AudioProcessor
from response import TextToSpeech, Gemini
from preset import YmlHandler
from youtube import Uploader
from media import Scraper
from video import Editor
from contextlib import contextmanager
import asyncio
import logging
import os
import shutil
import tempfile
from dotenv import load_dotenv
from pathlib import Path
from argparse import ArgumentParser

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(
    level=logging.DEBUG, format="%(levelname)s - %(message)s", force=True
)


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
        self.preset = YmlHandler(path)
        self.client = genai.Client(
            api_key=(
                self.preset.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
            )
        )
        self.workspace = Path(workspace)
        self.scraper = Scraper(workspace=self.workspace)
        self.video = Editor(self.workspace)
        self.tts = TextToSpeech(client=self.client, workspace=self.workspace)
        self.gemini = Gemini(client=self.client)
        self.audio_processor = AudioProcessor(
            workspace=self.workspace,
            model_size=self.preset.get("WHISPER_MODEL", default="small"),
            font=self.preset.get("FONT", default="Comic Sans MS"),
        )

        if self.preset.get("UPLOAD") is not False:
            self.uploader = Uploader(
                name=self.preset.get("NAME", default="crank"),
                auth_token=self.preset.get("OAUTH_PATH", "secrets.json"),
            )

    def _time_left(self, num_hours):
        limit_time = self.preset.get("LIMIT_TIME")
        if not limit_time:
            return 0
        limit_time_dt = datetime.datetime.fromisoformat(limit_time)
        elapsed = datetime.datetime.now(datetime.UTC) - limit_time_dt
        hours = datetime.timedelta(hours=num_hours)
        return int(max((hours - elapsed).total_seconds(), 0))

    def _upload(self, content, output_path):
        title = (
            self.gemini.get_response(
                f"{self.preset.get('GET_TITLE')}\n\n{content}", model=2.0
            )
            or "#shorts"
        )
        description = self.preset.get("DESCRIPTION", default="#shorts")
        try:
            self.preset.set(
                "LAST_UPLOAD",
                self.uploader.upload(
                    video_path=output_path,
                    title=title,
                    tags=self.preset.get("TAGS", default=[]),
                    description=description,
                    categoryId=self.preset.get("CATEGORY_ID", default=24),
                    delay=self.preset.get("DELAY", 0),
                    last_upload=self.preset.get("LAST_UPLOAD")
                    or datetime.datetime.now(datetime.UTC),
                ),
            )
        except ResumableUploadError:
            self.preset.set(
                "LIMIT_TIME", str(datetime.datetime.now(datetime.UTC).isoformat())
            )
            self.logger.warning("Upload limit reached")

        current = self.preset.get("USED_CONTENT") or []
        if title and title not in current:
            current.append(title.strip())
            self.preset.set("USED_CONTENT", current[-100:])

    async def run(self):
        while True:
            try:
                if hasattr(self, "uploader"):
                    time_left = self._time_left(num_hours=24)
                    while time_left > 0:
                        hours, minutes, seconds = (
                            time_left // 3600,
                            (time_left % 3600) // 60,
                            time_left % 60,
                        )
                        print(
                            f"\r[{self.preset.get('NAME')}] Crank will continue in {hours}h {minutes}m {seconds}s",
                            end="",
                        )
                        await asyncio.sleep(1)
                        time_left -= 1

                content = self.gemini.get_response(
                    query=f"{self.preset.get('CONTENT_PROMPT')}\n\nAvoid ALL topics even remotely related to: {self.preset.get('USED_CONTENT') or []}\n\n Return ONLY fresh content.",
                    model=2.0,
                )
                media_path = self.scraper.get_media(
                    self.gemini.get_response(
                        f"{self.preset.get('TERM_PROMPT')}\n{content}", model=2.5
                    )
                )
                audio_path = self.tts.get_audio(transcript=content)
                ass_path = self.audio_processor.get_captions(audio_path=audio_path)
                output_path = self.video.assemble(
                    ass_path=ass_path, audio_path=audio_path, media_path=media_path
                )

                if not hasattr(self, "uploader"):
                    break

                self._upload(content=content, output_path=output_path)
            except RuntimeError as e:
                self.logger.critical(e)
                break
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(e)


if __name__ == "__main__":
    load_dotenv()

    parser = ArgumentParser()
    parser.add_argument("--path", help="Path to config.yml", default="preset.yml")
    args = parser.parse_args()
    path = args.path

    with new_workspace() as workspace:
        core = Core(workspace, path)
        asyncio.run(core.run())
