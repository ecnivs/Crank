from settings import *

class VideoEditor:
    def __init__(self, duration=60):
        self.duration = max(1, duration)

    def _get_duration(self, video):
        if not os.path.exists(video):
            raise FileNotFoundError(f"[{self.__class__.__name__}] File not found: {video}")
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            video
        ]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            info = json.loads(output)

            if 'format' not in info or 'duration' not in info['format']:
                raise RuntimeError(f"[{self.__class__.__name__}] Could not extract duration from {video}")

            return float(info['format']['duration'])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"[{self.__class__.__name__}] FFprobe failed: {e.output.decode() if hasattr(e, 'output') else str(e)}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"[{self.__class__.__name__}] Failed to parse FFprobe output for {video}") from e

    def _get_frames(self):
        frames_dir = 'frames'
        if not os.path.isdir(frames_dir):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Directory not found: {frames_dir}")

        frames = []
        for file in os.listdir(frames_dir):
            if file.endswith(".wav"):
                frames.append(file)

        if not frames:
            raise ValueError(f"[{self.__class__.__name__}] No .wav files found in 'frames' directory")

        frames.sort(key=lambda f: int(re.search(r'(\d+)', f).group()))
        return [os.path.join(frames_dir, f) for f in frames]

    def _add_card(self, input_video, card, first_audio_duration, duration):
        for file_path, file_desc in [(input_video, "input video"), (card, "card image")]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"[{self.__class__.__name__}] {file_desc.capitalize()} not found: {file_path}")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_path = temp_file.name
        first_audio_duration = max(0.1, min(first_audio_duration, duration))

        cmd = [
            "ffmpeg",
            "-i", input_video,
            "-i", card,
            "-filter_complex",
            "[0:v]scale=iw:ih[scaled_input];"
            "[1:v]scale=iw*0.90:ih*0.8[card];"
            f"[scaled_input][card]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{first_audio_duration - 0.1})'[v]",
            "-map", "[v]",
            "-map", "0:a:0?",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-y", output_path
        ]
        try:
            logging.info(f"Running FFmpeg command to add card: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(f"Video generated successfully with card! Saved as {output_path}")

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError(f"[{self.__class__.__name__}] Failed to create output video (file is empty or doesn't exist)")

            if os.path.exists(input_video) and input_video != output_path:
                os.remove(input_video)
            return output_path

        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logging.error(f"FFmpeg failed: {error_output}")

            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError(f"[{self.__class__.__name__}] Failed to add card to video: {error_output}") from e

    def _has_audio(self, video_path):
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "json", video_path
        ]
        output = subprocess.check_output(cmd)
        info = json.loads(output)
        return bool(info.get("streams"))

    def generate_video(self, end_time, input_video, card, ass_file):
        if not os.path.exists(input_video):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Input video not found: {input_video}")
        if not os.path.exists(card):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Card image not found: {card}")
        if not os.path.exists(ass_file):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Subtitle file not found: {ass_file}")
        if end_time <= 0:
            raise ValueError(f"[{self.__class__.__name__}] End time must be positive")

        concat_list = None
        try:
            audio_files = self._get_frames()

            input_duration = self._get_duration(input_video)
            actual_end_time = min(end_time, self.duration, input_duration)
            if actual_end_time <= 0:
                raise ValueError(f"[{self.__class__.__name__}] Calculated video duration is not positive")

            first_audio_duration = self._get_duration(audio_files[0]) if audio_files else 1.0
            input_video = self._add_card(input_video, card, first_audio_duration, input_duration)

            concat_list = "concat_list.txt"
            with open(concat_list, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")

            has_audio = self._has_audio(input_video)

            cmd = ["ffmpeg", "-y", "-i", input_video, "-f", "concat", "-safe", "0", "-i", concat_list]

            if has_audio:
                filter_complex = "[0:a:0][1:a:0]amix=inputs=2:duration=longest:dropout_transition=0,aresample=async=1000[a]"
                cmd += [
                    "-filter_complex", filter_complex,
                    "-map", "0:v:0",
                    "-map", "[a]",
                ]
            else:
                cmd += [
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                ]

            cmd += [
                "-vf", f"ass={ass_file},scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-pix_fmt", "yuv420p",
                "-t", str(actual_end_time),
                "output.mp4"
            ]

            logging.info(f"Running final FFmpeg command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if os.path.exists(concat_list):
                os.remove(concat_list)
            if os.path.exists(input_video):
                os.remove(input_video)

            if not os.path.exists("output.mp4") or os.path.getsize("output.mp4") == 0:
                raise RuntimeError(f"[{self.__class__.__name__}] Failed to generate output video (file is empty or doesn't exist)")

            logging.info("✅ Short generated at output.mp4")
            return "output.mp4"

        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logging.error(f"FFmpeg command failed: {error_output}")
            if concat_list and os.path.exists(concat_list):
                os.remove(concat_list)
            if input_video and os.path.exists(input_video):
                os.remove(input_video)
            raise RuntimeError(f"[{self.__class__.__name__}] Error while generating video: {error_output}") from e

        except Exception as e:
            if concat_list and os.path.exists(concat_list):
                os.remove(concat_list)
            if input_video and os.path.exists(input_video):
                os.remove(input_video)
            raise RuntimeError(f"[{self.__class__.__name__}] Could not generate video: {e}") from e
