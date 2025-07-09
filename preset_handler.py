from settings import *

class PresetHandler:
    def __init__(self, preset_path, script = None, template = None):
        self.preset_path = preset_path
        self.data = self._load_data(self.preset_path)
        self.template = template or self._get("TEMPLATE", "")
        self.script = script or self._get("SCRIPT", "")
        self._on_init()

    def _on_init(self):
        self.name = self._get("NAME")
        self.upload = self._get("UPLOAD", False)
        self.save = self._get("SAVE", False)
        self.description = self._get("DESCRIPTION", "")
        self.tags = self._get("TAGS", [])
        self.intro_message = self._get("INTRO_MSG", "")
        self.voice = self._get("VOICE", DEFAULT_VOICE)
        self.prompt = self._get("PROMPT", {})
        self.sheet_id = self._get("SHEET_ID", "")
        self.category_id = self._get("CATEGORY", 27)
        self.pfp_path = self._get("PFP")
        self.audio = self._get("AUDIO", DEFAULT_AUDIO)
        self.used_content_count = self._get("USED_CONTENT_COUNT", 100)
        self.data.setdefault("USED_CONTENT", [])
        self.data.setdefault("PENDING", [])
        self.data.setdefault("LIMIT_TIME", "")

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
    def pending(self):
        return self.data["PENDING"]

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

    def add_to_pending(self, item):
        if item not in self.data["PENDING"] and self.prompt:
            self.data["PENDING"].append(item)
            self._write_data()

    def set_limit_time(self):
        if self.prompt:
            self.data["LIMIT_TIME"] = str(datetime.datetime.utcnow().isoformat())
            self._write_data()

    def get_pending(self):
        if self.data["PENDING"]:
            item = self.data["PENDING"].pop(0)
            self._write_data()
            return item
        return None

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
