import whisper
import os
from settings import *
import logging

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s - %(message)s',
                    force=True)

class CaptionHandler:
    def __init__(self, workspace, model_size):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = whisper.load_model(model_size)
        self.workspace = workspace
        self.header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dynamic, Arial, 48, &H00FFFFFF, &H000000FF, &H00000000, &H80000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 5, 10, 10, 20, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def _format_timestamp(self, ts):
        h = int(ts // 3600)
        m = int((ts % 3600) // 60)
        s = int(ts % 60)
        cs = int((ts - int(ts)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def get_captions(self, audio_path):
        result = self.model.transcribe(audio_path)
        path = os.path.join(self.workspace, 'captions.ass')
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.header)
            for segment in result.get("segments", []):
                start = self._format_timestamp(segment["start"])
                end = self._format_timestamp(segment["end"])
                text = segment["text"].strip()
                words = text.split()
                lines = []
                current_line = []

                for word in words:
                    current_line.append(word)
                    if len(current_line) >= 8:
                        lines.append(" ".join(current_line))
                        current_line = []
                if current_line:
                    lines.append(" ".join(current_line))
                formatted_text = "\\N".join(lines)
                f.write(f"Dialogue: 0,{start},{end},Dynamic,,0,0,0,,{formatted_text}\n")
        self.logger.info(f"ASS file stored at {path}")
        return path
