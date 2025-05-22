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
        self.video_editor = VideoEditor()
        self.speech_handler = SpeechHandler()
        self.caption_handler = CaptionHandler()
        self.media_handler = MediaHandler()
        self.card_handler = CardHandler()
        self.delay = DELAY

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
                video_path=video_path,
                title=video_title,
                description=description,
                tags=tags[:30],
                categoryId=self.preset.category_id
            )
            if cleaned_title not in self.preset.used_content:
                self.preset.add_to_used(cleaned_title)
        except Exception:
            logging.info(video_title, description, tags)
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
        logging.info(f"Used content: {used}")
        prompt = f"{self.preset.get_prompt()}\n\nAvoid ALL topics related to: {used}\nReturn ONLY fresh, unrelated content."
        return self.res_handler.gemini(prompt)

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
                return self.res_handler.gemini(f"Correct punctuation and spelling:\n{sheet_text}")
        if self.preset.prompt:
            logging.info(f"Generating content.")
            return self._get_content()
        return None

    def _generate_intro(self, captions):
        if self.preset.intro_message:
            return self.preset.intro_message
        return self.res_handler.gemini(captions, GET_INTRO)

    def run(self, preset = None, script = None, template = None):
        captions = None
        try:
            self.preset_path = f"presets/{preset}.json"
            self.preset = PresetHandler(self.preset_path, script, template)
            if self.preset.upload:
                self.youtube_handler = YoutubeHandler(self.preset.name.lower())

            while self.preset:
                captions = self._get_captions()
                if not captions:
                    logging.error("No content to process.")
                    break

                logging.info(f"Captions:\n{captions}")
                intro = self._generate_intro(captions)
                captions_list = [intro] + self._split_for_shorts(captions)

                for caption in captions_list:
                    self.speech_handler.add_text(caption)
 
                timeline = self.speech_handler.speak(self.preset.voice)
                end_time, ass_file = self.caption_handler.generate_ass(captions_list, timeline)
                path = self.media_handler.process_media(self.preset.template, end_time, self.preset.audio)
                card = self.card_handler.get_card(self.preset.name, intro, self.preset.pfp_path)
                self.video_editor.generate_video(end_time, path, card, ass_file)

                title = f"{self.res_handler.gemini(captions, GET_TITLE)} #shorts"
                if self.preset.upload:
                    self._upload(captions, title, intro)

                if self.preset.save:
                    self._save_video(title)

                if self.preset.script:
                    break

                logging.info(f"Sleeping for {self.delay} seconds before the next run...")
                time.sleep(self.delay)
                captions = None
        except KeyboardInterrupt:
            logging.info("Shutting down...")
        except ResumableUploadError:
            logging.error("Upload limit exceeded")
        except RuntimeError as e:
            logging.critical(e)
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
        finally:
            if captions:
                self.preset.add_to_pending(captions)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--preset", help="Select Preset")
    parser.add_argument("-s", "--script", help="Insert Script")
    parser.add_argument("-t", "--template", help="Select template")
    args = parser.parse_args()
    core = Core()
    core.run(args.preset, args.script, args.template)
