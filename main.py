from os import path
from googleapiclient.http import ResumableUploadError
from settings import *
from video_editor import VideoEditor
from res_handler import ResponseHandler
from speech_handler import SpeechHandler
from youtube_handler import YoutubeHandler
from caption_handler import CaptionHandler
from preset_handler import PresetHandler
from media_handler import MediaHandler
from card_handler import CardHandler
import argparse

class Core:
    def __init__(self):
        self.res_handler = ResponseHandler()
        self.video_editor = VideoEditor(duration=60.0)
        self.caption_handler = CaptionHandler()
        self.media_handler = MediaHandler()
        self.card_handler = CardHandler()
        self.delay = DELAY

    async def _load_speech_handler(self):
        self.speech_handler = await SpeechHandler.create()

    def _split_for_shorts(self, captions, max_words=20):
        if not captions or not isinstance(captions, str):
            return []
        sentences = re.split(r'(?<=[.!?,])\s+', captions)
        frames = []
        for sentence in sentences:
            words = sentence.split()
            while words:
                chunk = words[:max_words]
                frames.append(" ".join(chunk))
                words = words[max_words:]
        return frames

    def _add_disclaimer(self, description):
        if not self.preset.prompt:
            return description
        hashtag_pos = description.find("#")
        if hashtag_pos != -1:
            new_description = description[:hashtag_pos] + f"{DISCLAIMER}\n\n" + description[hashtag_pos:]
        else:
            new_description = description + DISCLAIMER
        return new_description

    def _upload(self, captions, video_title, intro_message):
        if not video_title or not isinstance(video_title, str):
            raise ValueError("Invalid video title provided.")

        description = self._add_disclaimer(self.preset.description or self.res_handler.gemini(captions, GET_DESCRIPTION))
        tags = [self.preset.tags or self.res_handler.gemini(f"{intro_message}: {description}", GET_TAGS).split(",")]

        cleaned_title = video_title.replace("#shorts", "").strip()
        video_path = getattr(self, "output_path", "output.mp4")

        try:
            self.youtube_handler.upload(
                channel_name=self.preset.name,
                video_path=video_path,
                title=video_title,
                description=description,
                tags=tags[:30],
                categoryId=self.preset.category_id
            )
            if cleaned_title not in self.preset.used_content:
                self.preset.add_to_used(cleaned_title)
        except Exception:
            raise

    def _save_video(self, video_title):
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_title)
        preset_folder = os.path.join("saved_videos", self.preset.name)
        os.makedirs(preset_folder, exist_ok=True)
        source_path = "output.mp4"
        destination = os.path.join(preset_folder, f"{safe_title}.mp4")

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Cannot save video: '{source_path}' does not exist.")
        try:
            shutil.move(source_path, destination)
        except Exception as e:
            raise IOError(f"[{self.__class__.__name__}] Failed to save video to '{destination}'") from e

    def _get_content(self):
        used = ", ".join(self.preset.used_content or [])
        if used:
            logging.info(f"Used content: {used}")
        return self.res_handler.gemini(self.preset.get_prompt(), f"{CONTENT_PROMPT}\n\nAvoid ALL topics related to: {used}\nReturn ONLY fresh, unrelated content.")

    def _get_captions(self):
        pending = self.preset.get_pending()
        if pending:
            return pending
        if self.preset.script:
            return self.preset.script
        if self.preset.sheet_id:
            logging.info(f"Fetching from sheet: {self.preset.sheet_id}")
            sheet_text = self.res_handler.get_sheet_response(self.preset.sheet_id)
            if sheet_text:
                return self.res_handler.gemini(sheet_text, prompt="Correct the punctuation and spelling.")
        if self.preset.prompt:
            logging.info(f"Generating content.")
            return self._get_content()
        return None

    def _generate_intro(self, captions):
        if self.preset.intro_message:
            return self.preset.intro_message
        return self.res_handler.gemini(captions, GET_INTRO)

    def _has_24_hours_passed(self):
        if not self.preset.limit_time:
            return True, datetime.timedelta(0)
        limit_time_dt = datetime.datetime.fromisoformat(self.preset.limit_time)
        elapsed = datetime.datetime.utcnow() - limit_time_dt
        time_left = datetime.timedelta(seconds=max(0, int((datetime.timedelta(hours=24) - (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(self.preset.limit_time))).total_seconds())))
        return (elapsed >= datetime.timedelta(hours=24)), max(time_left, datetime.timedelta(0))

    def _get_template(self, captions, end_time):
        tags = self.res_handler.gemini(f"(prompt:[{self.preset.get_prompt()}] content:[{captions}])", GET_SEARCH_TAGS).split(", ")
        max_results = min(-(-end_time // 5), 10)
        random.shuffle(tags)
        for tag in tags:
            urls = self.media_handler.lookup_templates(tag, max_results)
            if urls and len(urls) > (max_results * 0.7):
                result = self.media_handler.download_templates(urls)
                if result is not None:
                    return result

    async def _process_all(self, captions_list, intro):
        timeline = await self.speech_handler.speak(self.preset.voice)
        end_time, ass_file = await asyncio.to_thread(
            self.caption_handler.generate_ass, captions_list, timeline
        )
        path = self.preset.template or self._get_template(' '.join(captions_list), end_time)
        media_task = self.media_handler.process_media(end_time, path, self.preset.audio)
        card_task = asyncio.to_thread(
            self.card_handler.get_card, self.preset.name, intro, self.preset.pfp_path
        )
        path, card = await asyncio.gather(media_task, card_task)
        self.video_editor.generate_video(end_time, path, card, ass_file)

    async def run(self, preset = None, script = None, template = None, ignore = False):
        captions = None
        try:
            if not hasattr(self, 'speech_handler') or self.speech_handler is None:
                load_task = asyncio.create_task(self._load_speech_handler())
            else:
                load_task = asyncio.create_task(asyncio.sleep(0))

            self.preset_path = f"presets/{preset}.json"
            self.preset = PresetHandler(self.preset_path, script, template)

            if self.preset.upload:
                has_24_hours_passed, time_left = self._has_24_hours_passed()
                if not has_24_hours_passed and not self.preset.save and not ignore:
                    load_task.cancel()
                    raise OnCooldown(f"Wait for {time_left} before proceeding.")
                elif not has_24_hours_passed and self.preset.save and not ignore:
                    self.youtube_handler = None
                else:
                    self.youtube_handler = YoutubeHandler(self.preset.name.lower())

            while self.preset:
                captions = self._get_captions()
                if not captions:
                    logging.error("No content to process.")
                    load_task.cancel()
                    break

                logging.info(f"Captions:\n{captions}")
                intro = self._generate_intro(captions)
                captions_list = [intro] + self._split_for_shorts(captions)
                title = f"{self.res_handler.gemini(captions, GET_TITLE)} #shorts"

                await load_task
                for caption in captions_list:
                    self.speech_handler.add_text(caption)
                await self._process_all(captions_list, intro)

                if self.preset.upload and self.youtube_handler:
                    self._upload(captions, title, intro)
                if self.preset.save:
                    self._save_video(title)
                if self.preset.script:
                    break

                logging.info(f"Sleeping for {self.delay} seconds before the next run...")
                await asyncio.sleep(self.delay)
                captions = None
        except KeyboardInterrupt:
            logging.info("Shutting down...")
        except ResumableUploadError as e:
            logging.error(f"Upload limit exceeded: {e}")
            self.preset.set_limit_time()
        except OnCooldown as e:
            logging.error(e)
        except RuntimeError as e:
            logging.critical(e)
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
        finally:
            if captions and not self.preset.prompt:
                self.preset.add_to_pending(captions)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--preset", help="Select preset")
    parser.add_argument("-s", "--script", help="Insert script")
    parser.add_argument("-t", "--template", help="Select template")
    parser.add_argument("--ignore", help="Ignore cooldown")
    args = parser.parse_args()
    core = Core()
    asyncio.run(core.run(args.preset, args.script, args.template, args.ignore))
