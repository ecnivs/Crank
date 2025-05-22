from settings import *
from pathlib import Path

class MediaHandler:
    def __init__(self, output_width=1080, output_height=1920, fps=30, duration=60):
        self.output_width = output_width
        self.output_height = output_height
        self.fps = fps
        self.duration = duration
        self.supported_exts = ['.mp4', '.mov', '.avi', '.mkv']

    async def process_media(self, path, end_time, audio_path=None):
        self.duration = end_time
        if not os.path.exists(path):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Path does not exist: {path}")

        output_path = self._create_output_path()
        logging.info(f"Processing media from {path}, audio from {audio_path}")
        logging.info(f"Output will be saved to {output_path}")
        try:
            if os.path.isdir(path):
                output = await asyncio.to_thread(self._process_folder, path, output_path)
            else:
                output = await asyncio.to_thread(self._process_video, path, output_path)

            logging.info(f"Video processing complete: {output}")
            await asyncio.sleep(0.1)

            if audio_path and os.path.exists(audio_path):
                logging.info(f"Adding audio from {audio_path}")
                await asyncio.to_thread(self._add_audio, output, audio_path)
                logging.info("Audio added successfully")

            return output
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] Error processing media") from e

    def _process_video(self, video_path, output_path):
        ext = os.path.splitext(video_path.lower())[1]
        if ext not in self.supported_exts:
            raise ValueError(f"[{self.__class__.__name__}] Unsupported file type: {ext}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            raise ValueError(f"[{self.__class__.__name__}] Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        duration = total_frames / fps
        if duration >= self.duration:
            self._copy_video(video_path, output_path)
        else:
            loops_needed = int(np.ceil(self.duration / duration))
            self._loop_video(video_path, output_path, loops_needed)
        return output_path

    def _process_folder(self, folder_path, output_path):
        video_files = self._get_video_files(folder_path)
        if not video_files:
            raise ValueError(f"[{self.__class__.__name__}] No supported video files in: {folder_path}")

        valid_videos = []
        video_durations = {}
        for video_path in video_files:
            abs_path = os.path.abspath(str(video_path))
            if not os.path.exists(abs_path) or not os.access(abs_path, os.R_OK):
                continue

            cap = cv2.VideoCapture(abs_path)
            if not cap.isOpened():
                cap.release()
                continue

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()

            duration = total_frames / fps
            if duration < 5:
                continue

            valid_videos.append(abs_path)
            video_durations[abs_path] = duration

        if not valid_videos:
            raise ValueError(f"[{self.__class__.__name__}] No valid video files found or accessible")

        temp_dir = os.path.join(tempfile.gettempdir(), "video_clips")
        os.makedirs(temp_dir, exist_ok=True)

        clip_paths = []
        total_duration = 0
        selected_videos = set()

        while total_duration < self.duration:
            if len(selected_videos) == len(valid_videos):
                selected_videos = set()

            video_path = random.choice(valid_videos)
            if video_path in selected_videos:
                continue
            selected_videos.add(video_path)

            duration = video_durations[video_path]
            cap = cv2.VideoCapture(video_path)
            start_frame = random.randint(0, max(0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 5 * self.fps))
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            frames = []
            for _ in range(5 * self.fps):
                ret, frame = cap.read()
                if not ret:
                    break
                frame_resized = cv2.resize(frame, (self.output_width, self.output_height))
                frames.append(frame_resized)
            cap.release()

            if len(frames) < 5 * self.fps:
                continue

            clip_path = os.path.join(temp_dir, f"clip_{len(clip_paths)}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(clip_path, fourcc, self.fps, (self.output_width, self.output_height))
            for frame in frames:
                out.write(frame)
            out.release()

            clip_paths.append(clip_path)
            total_duration += 5

        intermediate_file = os.path.join(tempfile.gettempdir(), "intermediate.txt")
        with open(intermediate_file, 'w') as f:
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.output_width, self.output_height))
        for clip_path in clip_paths:
            cap = cv2.VideoCapture(clip_path)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            cap.release()
        out.release()

        for clip_path in clip_paths:
            if os.path.exists(clip_path):
                os.remove(clip_path)
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
        return output_path

    def _get_video_files(self, folder_path):
        video_files = []
        for ext in self.supported_exts:
            video_files.extend(Path(folder_path).glob(f'*{ext}'))
            video_files.extend(Path(folder_path).glob(f'*{ext.upper()}'))
        return video_files

    def _copy_video(self, input_path, output_path):
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vf", f"scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=decrease,pad={self.output_width}:{self.output_height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-r", str(self.fps),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "copy",
            output_path
        ]
        subprocess.run(cmd, check=True)

    def _loop_video(self, input_path, output_path, loops):
        concat_list_path = os.path.join(tempfile.gettempdir(), "loop_list.txt")
        abs_input_path = os.path.abspath(input_path)

        with open(concat_list_path, 'w') as f:
            for _ in range(loops):
                f.write(f"file '{abs_input_path}'\n")

        temp_concat = output_path + "_concat.mp4"
        cmd_concat = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-segment_time_metadata", "1",
            "-i", concat_list_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-r", str(self.fps),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-t", str(self.duration),
            "-c:a", "aac",
            temp_concat
        ]
        try:
            subprocess.run(cmd_concat, check=True)
            os.replace(temp_concat, output_path)
        finally:
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
            if os.path.exists(temp_concat) and os.path.exists(output_path):
                os.remove(temp_concat)

    def _add_audio(self, video_path, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"[{self.__class__.__name__}] Audio path does not exist: {audio_path}")

        temp_output = video_path + "_with_audio.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-stream_loop", "-1",
            "-i", audio_path,
            "-filter:a", "volume=0.25",
            "-shortest",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            temp_output
        ]
        try:
            subprocess.run(cmd, check=True)
            os.replace(temp_output, video_path)
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def _create_output_path(self):
        return os.path.join(tempfile.gettempdir(), "processed_video.mp4")
