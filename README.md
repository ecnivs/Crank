# Crank 🎬
> Shorts without sweat. Crank it.

**Crank** is an automated YouTube Shorts generator built for speed, customization, and scalability. It uses presets to rapidly produce high-quality Shorts with zero manual editing.

## ✨ Features
- Fully automated shorts creation  
- Preset-driven configuration system  
- Prompt-based script generation with optional static scripts  
- TTS voice synthesis integration  
- Dynamic background templates (video or directory of clips)  
- Auto-generated metadata (description, tags, intros) with manual override  
- Batch processing with Google Sheets integration

## 🛠️ Prerequisites
- Python 3.x (Tested with Python 3.11 using `pyenv`)
- Required Python libraries (listed in `requirements.txt`)
- The `video_editor` Python extension module (built from Rust source)
- `ffmpeg` and `ffprobe` installed and available in your system PATH (required for video processing)  
- Google API credentials for Google Sheets and YouTube automation (stored as JSON files, see below)
- Voice files compatible with your setup for one-shot voice cloning (WAV samples)

#### Environment Variables
Crank uses a .env file to load sensitive keys and config values.
Make sure to create a .env file in the root directory containing your API keys, for example:
```ini
GEMINI_API_KEY=your_api_key_here
```

#### Credential Files
The other credentials are stored as JSON files inside the `json/` directory:
- `json/key.json` — Google Service Account JSON used by `gspread` for Google Sheets access
- `json/secrets.json` — OAuth 2.0 client credentials JSON used for YouTube API upload authentication

#### Presets
Presets define your shorts' configuration (scripts, voices, backgrounds, styles).
Store each preset as a JSON file inside the `presets/` folder.
This makes it easy to manage multiple themes or channels without changing code.

Make sure these files exist and your code references their correct paths.

### 🧩 Preset System
Crank uses JSON-based presets to control how shorts are generated. Each preset is a self-contained config that defines script behavior, media, voice, style, and metadata.

Below is a breakdown of all supported fields:

| Field         | Type     | Description |
|---------------|----------|-------------|
| `NAME`        | `string` | Internal identifier for the preset. Used for logging or UI display. |
| `PROMPT`      | `string` | Prompt sent to the language model to generate the script. Ignored if `SCRIPT` is used. |
| `VOICE`       | `string` | Path to the TTS voice file (e.g., `voices/speaker.wav`). |
| `AUDIO`       | `string` | Optional background music or ambience (e.g., `audio/piano.wav`). |
| `UPLOAD`      | `boolean`| If true, the final video will be flagged for upload. |
| `CATEGORY`    | `int`    | YouTube category ID (e.g., 22 for People & Blogs). |
| `TEMPLATE`    | `string` | Optional path to a video file or a directory. If it’s a directory, Crank randomly picks clips from the videos inside to compose the background and transitions dynamically. This allows flexible, varied visual templates without manual video editing. Auto-generated if not provided. |
| `PFP`         | `string` | Path to the profile image used in the video. |
| `USED_CONTENT`| `array`  | Managed by Crank. Tracks what content has already been used. |
| `LIMIT_TIME`  | `string` | Managed by Crank. Tracks the timestamp of the last `ResumableUploadError` caused by quota limits. Used to check if the cooldown period has passed before attempting another upload. |

#### Notes

- `USED_CONTENT` and `LIMIT_TIME` are modified by Crank during runtime. Do not edit them manually unless you're clearing the state.
- If `PROMPT` is empty, the preset will fail to generate anything.
- Paths are relative to the Crank root directory unless absolute.

You can define multiple presets for different channels, formats, or content styles and switch between them instantly.

#### 🔧 Example Preset
```json
{
  "NAME": "Crank",
  "PROMPT": "Generate a test script for a youtube short.",
  "VOICE": "voices/speaker.wav",
  "AUDIO": "audio/piano.wav",
  "UPLOAD": false,
  "CATEGORY": 22,
  "TEMPLATE": "templates/",
  "PFP": "",
  "USED_CONTENT": [],
  "LIMIT_TIME": ""
}
```

## ⚙️ Installation
1. **Clone the repository**
```bash
git clone https://github.com/ecnivs/crank.git
cd crank
```
2. **Set up Python with `pyenv`**
```bash
pyenv install 3.11
pyenv local 3.11
```
3. **Install dependencies**
```bash
pip install -r requirements.txt
```
4. **Install `ffmpeg`**
```bash
# Debian / Ubuntu
sudo apt install ffmpeg  # debian

# Arch Linux
sudo pacman -S ffmpeg  # arch

# macOS (Homebrew)
brew install ffmpeg  # macos

# Windows (using Chocolatey)
choco install ffmpeg  # windows
```

#### Build and install the Rust extension modules
For any Rust-based Python extension module in this project, follow these steps:
```bash
cd <module_directory>
maturin build --release
pip install target/wheels/<module_name>-*.whl
```
- Replace `<module_directory>` with the folder containing the Rust module you want to build.
- Replace `<module_name>` with the crate name of the Rust module (usually matches the folder name).

You **must** repeat this process for each Rust extension module included in the project.

## 🚀 Running Crank
After installation and setup, you can run Crank from the command line using:
```bash
python main.py -p <preset_name> [-s <script>] [-t <template_path>]
```
#### Arguments:
- `-p, --preset` (required): Name of the preset (without .json, must exist inside presets/)
- `-s, --script` (optional): Custom script text (overrides auto-generated content)
- `-t, --template` (optional): Path to a specific template (overrides what's in the preset)

#### Example:
```bash
python main.py -p example
```

## 💖 Support the project
If you find Crank helpful and want to support its development, donations are welcome!  
Your support helps keep the project active and enables new features.
<div align="center">
  <a href="https://www.buymeacoffee.com/ecnivs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</div>

## 🙌 Contributing
We appreciate any feedback or code reviews! Feel free to:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Submit a pull request

### I'd appreciate any feedback or code reviews you might have!
