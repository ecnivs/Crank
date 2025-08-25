from settings import *
import random
import json
import os
import datetime
from youtube_handler import YoutubeHandler

class PresetHandler:
    def __init__(self, preset_path):
        self.preset_path = preset_path
        self.data = self._load_data(self.preset_path)
        self.template = self._get("TEMPLATE", "")
        self._on_init()

    def _on_init(self):
        self.name = self._get("NAME")
        self.upload = self._get("UPLOAD", False)
        self.voice = self._get("VOICE", random.choice(self._load_files("voices")))
        self.prompt = self._get("PROMPT", {})
        self.category_id = self._get("CATEGORY", 27)
        self.pfp_path = self._get("PFP")
        self.audio = self._get("AUDIO", random.choice(self._load_files("audio")))
        self.used_content_count = self._get("USED_CONTENT_COUNT", 100)
        self.data.setdefault("USED_CONTENT", [])
        self.data.setdefault("LIMIT_TIME", "")
        self.youtube_handler = YoutubeHandler(self.name.lower())

    def _load_files(self, folder):
        files = []
        for file in os.listdir(folder):
            if file.endswith(".wav"):
                files.append(os.path.join(folder, file))
        return files

    def _load_data(self, path):
        try:
            with open(path, 'r') as file:
                logging.info(f"Loaded preset: {path}")
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"[{self.__class__.__name__}] {path} does not exist.")
        except json.JSONDecodeError:
            raise ValueError(f"[{self.__class__.__name__}] Error decoding JSON from {path}")

    def _get(self, key, default=None):
        return self.data.get(key, default)

    @property
    def used_content(self):
        return self.data["USED_CONTENT"]

    @property
    def limit_time(self):
        return self.data["LIMIT_TIME"]

    def add_to_used(self, item):
        if item not in self.data["USED_CONTENT"] and self.prompt:
            self.data["USED_CONTENT"].append(item)
            excess = len(self.data["USED_CONTENT"]) - self.used_content_count
            if excess > 0:
                self.data["USED_CONTENT"] = self.data["USED_CONTENT"][excess:]
            self._write_data()

    def set_limit_time(self):
        if self.prompt:
            self.data["LIMIT_TIME"] = str(datetime.datetime.utcnow().isoformat())
            self._write_data()

    def get_prompt(self):
        if isinstance(self.prompt, dict):
            return random.choice(list(self.prompt.values()))
        elif isinstance(self.prompt, str):
            return self.prompt
        else:
            raise ValueError(f"[{self.__class__.__name__}] Invalid PROMPT format in preset")

    def _write_data(self):
        try:
            with open(self.preset_path, 'w') as file:
                json.dump(self.data, file, indent=4)
                logging.info(f"Preset updated: {self.preset_path}")
        except Exception as e:
            logging.error(f"Failed to write preset data: {e}")
