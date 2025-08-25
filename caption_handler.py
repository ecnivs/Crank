from settings import *

class CaptionHandler:
    def __init__(self, duration=60):
        temp_dir = tempfile.gettempdir()
        self.ass_file = os.path.join(temp_dir, "captions.ass")
        self.duration = duration
        self.TIMING_OFFSET = -0.12

    def _time_to_str(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        cs = int((td.total_seconds() - total_seconds) * 100)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours}:{minutes:02}:{secs:02}.{cs:02}"

    def _animated_word(self, word):
        return f"{{\\fad(100,100)\\fscx60\\fscy60\\c&HFF0000&\\t(0,200,\\fscx100\\fscy100\\c&HFFFF00&)}}{word}"

    def _allocate_durations(self, words, total_duration, min_duration=0.1):
        char_lengths = [len(word) for word in words]
        total_chars = sum(char_lengths)
        if total_chars == 0:
            return [min_duration] * len(words)

        raw_durations = [(l / total_chars) * total_duration for l in char_lengths]
        clamped_durations = []
        excess = 0

        for dur in raw_durations:
            if dur < min_duration:
                excess += (min_duration - dur)
                clamped_durations.append(min_duration)
            else:
                clamped_durations.append(dur)

        remaining_indices = [i for i, dur in enumerate(raw_durations) if dur >= min_duration]
        if remaining_indices and excess > 0:
            total_remaining = sum(raw_durations[i] for i in remaining_indices)
            scale_factor = (total_remaining - excess) / total_remaining if total_remaining > excess else 0.001
            for i in remaining_indices:
                clamped_durations[i] = raw_durations[i] * scale_factor
        return clamped_durations

    def generate_ass(self, captions_list, timeline):
        if not captions_list:
            raise ValueError(f"[{self.__class__.__name__}] Caption list cannot be empty.")
        if len(timeline) < len(captions_list) + 1:
            raise ValueError(f"[{self.__class__.__name__}] Timeline must have at least one more element than captions.")

        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dynamic, Luckiest Guy, 90, &H00FFFF00, &H000000FF, &H00000000, &H96000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 4, 3, 5, 80, 80, 40, 1

[Events]
Format: Layer, Start, End, Style, Text
"""
        caption_lines = []
        for idx, caption_text in enumerate(captions_list[1:], start=1):
            start_time = timeline[idx]
            end_time = timeline[idx + 1]
            total_duration = end_time - start_time
            words = caption_text.strip().split()
            if not words:
                continue

            durations = self._allocate_durations(words, total_duration)
            current_time = start_time
            for word, duration in zip(words, durations):
                w_start = max(0, current_time + self.TIMING_OFFSET)
                w_end = max(w_start + 0.01, w_start + duration)
                animated = self._animated_word(word)
                line = f"Dialogue: 0,{self._time_to_str(w_start)},{self._time_to_str(w_end)},Dynamic,{animated}"
                caption_lines.append(line)
                current_time += duration

        video_end_time = min(timeline[-1], self.duration)
        try:
            os.makedirs(os.path.dirname(self.ass_file), exist_ok=True)
            with open(self.ass_file, "w", encoding="utf-8") as f:
                f.write(header)
                f.write("\n".join(caption_lines))
            logging.info(f"✅ ASS file generated at {self.ass_file}")
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] Failed to write ASS file") from e
        return video_end_time, self.ass_file
