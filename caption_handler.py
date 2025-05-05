from settings import *

class CaptionHandler:
    def __init__(self, duration = 60):
        temp_dir = tempfile.gettempdir()
        self.ass_file = os.path.join(temp_dir, "captions.ass")
        self.duration = duration

    def _time_to_str(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        cs = int((td.total_seconds() - total_seconds) * 100)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours}:{minutes:02}:{secs:02}.{cs:02}"

    def generate_ass(self, captions, timeline):
        if not captions:
            raise ValueError("Caption list cannot be empty.")

        if len(timeline) < len(captions) + 1:
            raise ValueError("Timeline must have at least one more element than captions.")

        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dynamic, Mono, 65, &H00FFFFFF, &H00000000, &H00000000, &H64000000, 1, 0, 0, 0, 100, 100, -0.2, 0, 1, 2, 1, 5, 80, 80, 40, 1

[Events]
Format: Layer, Start, End, Style, Text
"""

        caption_lines = []
        for idx, caption_text in enumerate(captions[1:], start=1):
            start_time = timeline[idx]
            end_time = timeline[idx + 1]
            line = f"Dialogue: 0,{self._time_to_str(start_time)},{self._time_to_str(end_time)},Dynamic,{caption_text}"
            caption_lines.append(line)

        video_end_time = min(timeline[-1], self.duration)

        try:
            os.makedirs(os.path.dirname(self.ass_file), exist_ok=True)
            with open(self.ass_file, "w", encoding="utf-8") as f:
                f.write(header)
                f.write("\n".join(caption_lines))
            logging.info(f"✅ ASS file generated at {self.ass_file}")
        except Exception as e:
            logging.error(f"❌ Failed to write ASS file: {e}")
            raise

        time.sleep(0.1)
        return video_end_time, self.ass_file
