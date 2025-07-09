use pyo3::prelude::*;
use pyo3::exceptions;
use std::path::Path;
use std::process::Command;
use serde_json::Value;
use glob::glob;
use regex::Regex;
use tempfile::NamedTempFile;
use std::fs::{self, File};
use std::io::Write;

#[pyclass]
struct VideoEditor {
    duration: f64,
}

#[pymethods]
impl VideoEditor {
    #[new]
    fn new(duration: Option<f64>) -> Self {
        Self {
            duration: duration.unwrap_or(60.0).max(1.0),
        }
    }

    fn _get_duration(&self, video: &str) -> PyResult<f64> {
        if !Path::new(video).exists() {
            return Err(exceptions::PyFileNotFoundError::new_err(format!("File not found: {}", video)));
        }

        let output = Command::new("ffprobe")
            .args([
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video
            ])
            .output()
            .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to run ffprobe: {}", e)))?;

        if !output.status.success() {
            return Err(exceptions::PyRuntimeError::new_err(format!(
                "ffprobe failed: {}",
                String::from_utf8_lossy(&output.stderr)
            )));
        }

        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let json: Value = serde_json::from_str(&stdout_str)
            .map_err(|_| exceptions::PyRuntimeError::new_err("Failed to parse ffprobe JSON output"))?;

        let duration = json.get("format")
            .and_then(|f| f.get("duration"))
            .and_then(|d| d.as_str())
            .ok_or_else(|| exceptions::PyRuntimeError::new_err("Could not extract duration from ffprobe output"))?;

        duration.parse::<f64>()
            .map_err(|_| exceptions::PyRuntimeError::new_err("Invalid duration format"))
    }

    fn _get_frames(&self) -> PyResult<Vec<String>> {
        let mut frames: Vec<String> = Vec::new();
        let re = Regex::new(r"(\d+)").unwrap();

        for entry in glob("frames/*.wav").map_err(|e| exceptions::PyRuntimeError::new_err(e.to_string()))? {
            match entry {
                Ok(path) => frames.push(path.to_string_lossy().to_string()),
                Err(e) => return Err(exceptions::PyRuntimeError::new_err(format!("Glob error: {}", e))),
            }
        }

        if frames.is_empty() {
            return Err(exceptions::PyValueError::new_err("No .wav files found in 'frames' directory"));
        }

        frames.sort_by_key(|f| {
            re.captures(f)
                .and_then(|cap| cap.get(1))
                .and_then(|m| m.as_str().parse::<i32>().ok())
                .unwrap_or(0)
        });

        Ok(frames)
    }

    fn _add_card(&self, input_video: &str, card: &str, first_audio_duration: f64, duration: f64) -> PyResult<String> {
        for (file_path, desc) in &[(input_video, "input video"), (card, "card image")] {
            if !Path::new(file_path).exists() {
                return Err(exceptions::PyFileNotFoundError::new_err(format!("{} not found: {}", desc, file_path)));
            }
        }

        let temp_file = NamedTempFile::new()
            .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to create temp file: {}", e)))?;
        let output_path = temp_file.path().with_extension("mp4");

        let first_audio_duration = first_audio_duration.clamp(0.1, duration);
        let filter_complex = format!(
            "[0:v]scale=iw:ih[scaled_input];[1:v]scale=iw*0.90:ih*0.8[card];[scaled_input][card]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{:.1})'[v]",
            first_audio_duration - 0.1
        );
        let status = Command::new("ffmpeg")
            .args([
                "-i", input_video,
                "-i", card,
                "-filter_complex", &filter_complex,
                "-map", "[v]",
                "-map", "0:a:0?",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                "-t", &duration.to_string(),
                "-y",
                output_path.to_str().unwrap(),
            ])
            .status()
            .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to run ffmpeg: {}", e)))?;

        if !status.success() {
            return Err(exceptions::PyRuntimeError::new_err("FFmpeg failed during _add_card"));
        }

        if !output_path.exists() || fs::metadata(&output_path).map(|m| m.len()).unwrap_or(0) == 0 {
            return Err(exceptions::PyRuntimeError::new_err("Output video from _add_card is empty or missing"));
        }
        Ok(output_path.to_string_lossy().to_string())
    }

    fn _has_audio(&self, video_path: &str) -> PyResult<bool> {
        let output = Command::new("ffprobe")
            .args([
                "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                video_path
            ])
            .output()
            .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to run ffprobe: {}", e)))?;

        if !output.status.success() {
            return Err(exceptions::PyRuntimeError::new_err(format!(
                "ffprobe failed: {}",
                String::from_utf8_lossy(&output.stderr)
            )));
        }

        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let json: Value = serde_json::from_str(&stdout_str)
            .map_err(|_| exceptions::PyRuntimeError::new_err("Failed to parse ffprobe JSON output"))?;

        Ok(json.get("streams").and_then(|s| s.as_array()).map(|arr| !arr.is_empty()).unwrap_or(false))
    }

    fn generate_video(&self, end_time: f64, input_video: &str, card: &str, ass_file: &str) -> PyResult<String> {
        if !Path::new(input_video).exists() {
            return Err(exceptions::PyFileNotFoundError::new_err(format!("Input video not found: {}", input_video)));
        }
        if !Path::new(card).exists() {
            return Err(exceptions::PyFileNotFoundError::new_err(format!("Card image not found: {}", card)));
        }
        if !Path::new(ass_file).exists() {
            return Err(exceptions::PyFileNotFoundError::new_err(format!("Subtitle file not found: {}", ass_file)));
        }
        if end_time <= 0.0 {
            return Err(exceptions::PyValueError::new_err("End time must be positive"));
        }

        let audio_files = self._get_frames()?;

        let input_duration = self._get_duration(input_video)?;
        let actual_end_time = end_time.min(self.duration).min(input_duration);
        if actual_end_time <= 0.0 {
            return Err(exceptions::PyValueError::new_err("Calculated video duration is not positive"));
        }

        let first_audio_duration = if !audio_files.is_empty() {
            self._get_duration(&audio_files[0])?
        } else {
            1.0
        };

        let input_video_with_card = self._add_card(input_video, card, first_audio_duration, input_duration)?;
        let concat_list_path = "concat_list.txt";
        {
            let mut concat_file = File::create(concat_list_path)
                .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to create concat_list.txt: {}", e)))?;
            for audio_file in &audio_files {
                writeln!(concat_file, "file '{}'", audio_file)
                    .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to write concat list: {}", e)))?;
            }
        }

        let has_audio = self._has_audio(&input_video_with_card)?;
        let mut cmd = vec![
            "-y".into(),
            "-i".into(),
            input_video_with_card.clone(),
            "-f".into(),
            "concat".into(),
            "-safe".into(),
            "0".into(),
            "-i".into(),
            concat_list_path.into(),
        ];

        if has_audio {
            cmd.push("-filter_complex".into());
            cmd.push("[0:a:0][1:a:0]amix=inputs=2:duration=longest:dropout_transition=0,aresample=async=1000[a]".into());
            cmd.push("-map".into());
            cmd.push("0:v:0".into());
            cmd.push("-map".into());
            cmd.push("[a]".into());
        } else {
            cmd.push("-map".into());
            cmd.push("0:v:0".into());
            cmd.push("-map".into());
            cmd.push("1:a:0".into());
        }

        cmd.extend_from_slice(&[
            "-t".into(),
            actual_end_time.to_string(),
            "-c:v".into(),
            "libx264".into(),
            "-preset".into(),
            "fast".into(),
            "-crf".into(),
            "22".into(),
            "-c:a".into(),
            "aac".into(),
            "-b:a".into(),
            "192k".into(),
            "-vf".into(),
            format!("subtitles={}", ass_file),
            "output.mp4".into(),
        ]);

        let status = Command::new("ffmpeg")
            .args(&cmd)
            .status()
            .map_err(|e| exceptions::PyRuntimeError::new_err(format!("Failed to run ffmpeg: {}", e)))?;

        let _ = fs::remove_file(concat_list_path);
        let _ = fs::remove_file(input_video_with_card);

        if !status.success() {
            return Err(exceptions::PyRuntimeError::new_err("FFmpeg failed during final video generation"));
        }

        Ok("output.mp4".to_string())
    }
}

#[pymodule]
fn video_editor(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VideoEditor>()?;
    Ok(())
}
