from settings import *
from video_editor import VideoEditor
from res_handler import ResponseHandler
from speech_handler import SpeechHandler
from caption_handler import CaptionHandler
from preset_handler import PresetHandler
from media_handler import MediaHandler
from card_handler import CardHandler
from plyer import notification

class Core:
    def __init__(self):
        self.res_handler = ResponseHandler()
        self.video_editor = VideoEditor(duration=60.0)
        self.caption_handler = CaptionHandler()
        self.media_handler = MediaHandler()
        self.card_handler = CardHandler()
        self.presets = self._load_all_presets("presets")
        self.delay = DELAY

    async def _load_speech_handler(self):
        self.speech_handler = await SpeechHandler.create()

    def _load_all_presets(self, folder):
        presets = []
        for file in os.listdir(folder):
            if file.endswith(".json"):
                presets.append(PresetHandler(os.path.join(folder, file)))
        return presets

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

    def _upload(self, captions, video_title, intro_message):
        if not video_title or not isinstance(video_title, str):
            raise ValueError("Invalid video title provided.")

        description = self.res_handler.gemini(captions, GET_DESCRIPTION)
        tags = [self.res_handler.gemini(f"{intro_message}: {description}", GET_TAGS).split(",")]

        cleaned_title = video_title.replace("#shorts", "").strip()
        video_path = getattr(self, "output_path", "output.mp4")

        self.preset.youtube_handler.upload(
            channel_name = self.preset.name,
            video_path = video_path,
            title = video_title,
            description = description,
            tags = tags[:30],
            categoryId = self.preset.category_id,
            preset = self.preset,
        )
        if cleaned_title not in self.preset.used_content:
            self.preset.add_to_used(cleaned_title)

    def _get_content(self):
        used = ", ".join(self.preset.used_content or [])
        if used:
            logging.info(f"Used content: {used}")
        return (self.res_handler.gemini(self.preset.get_prompt(), f"{CONTENT_PROMPT}\n\nAvoid ALL topics related to: {used}\nReturn ONLY fresh, unrelated content."))

    def _get_captions(self):
        if self.preset.prompt:
            logging.info(f"Generating content.")
            return self._get_content()
        return None

    def _generate_intro(self, captions):
        return self.res_handler.gemini(captions, GET_INTRO)

    def _has_24h_passed(self, preset):
        if not preset.limit_time:
            return True, datetime.timedelta(0)
        limit_time_dt = datetime.datetime.fromisoformat(preset.limit_time)
        elapsed = datetime.datetime.utcnow() - limit_time_dt
        return elapsed >= datetime.timedelta(hours=24)

    def _get_least_time_left(self):
        least_time_left = None
        now = datetime.datetime.utcnow()

        for preset in self.presets:
            if not preset.limit_time:
                continue
            try:
                limit_time_dt = datetime.datetime.fromisoformat(preset.limit_time)
            except ValueError:
                logging.warning(f"Invalid limit_time for preset: {preset}")
                continue

            elapsed = now - limit_time_dt
            elapsed_seconds = elapsed.total_seconds()
            time_left = max(0, 24*3600 - elapsed_seconds)

            if least_time_left is None or time_left < least_time_left:
                least_time_left = time_left

        if least_time_left is None:
            return 10
        return max(10, int(least_time_left))

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

    def _notify(self, title, message, app_name = "Crank", timeout = 10):
        notification.notify(title = title, message = message, app_name = app_name, timeout = timeout)

    async def run(self):
        try:
            self._notify("Welcome Back!", "YT Shorts generation in progress.")
            while self.presets:
                if not hasattr(self, 'speech_handler') or self.speech_handler is None:
                    load_task = asyncio.create_task(self._load_speech_handler())
                else:
                    load_task = asyncio.create_task(asyncio.sleep(0))

                for preset in [p for p in self.presets if self._has_24h_passed(p)]:
                    self.preset = preset

                    captions = self._get_captions()
                    if not captions:
                        logging.error("No prompt")
                        load_task.cancel()
                        continue

                    logging.info(f"Captions:\n{captions}")
                    intro = self._generate_intro(captions)
                    captions_list = [intro] + self._split_for_shorts(captions)
                    title = f"{self.res_handler.gemini(captions, GET_TITLE)}"

                    await load_task
                    for caption in captions_list:
                        self.speech_handler.add_text(caption)
                    await self._process_all(captions_list, intro)

                    if self.preset.upload and self.preset.youtube_handler:
                        self._upload(captions, title, intro)

                    least_time_left = self._get_least_time_left()
                    if least_time_left >= 120:
                        self.speech_handler = None

                    logging.info(f"Crank will continue in {least_time_left} secs")
                    await asyncio.sleep(least_time_left)
        except RuntimeError as e:
            logging.critical(e)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
        except Exception as e:
            logging.error(e)

if __name__ == "__main__":
    core = Core()
    asyncio.run(core.run())
