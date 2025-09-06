<h1 align="center">Crank</h1>
<p align="center"><em>Youtube Shorts Generator</em></p>

![IMG_20250901_182631](https://github.com/user-attachments/assets/2c272049-acc0-4b50-9b69-67c71cadf07e)

<p align="center">
  <a href="https://github.com/ecnivs/crank/stargazers">
    <img src="https://img.shields.io/github/stars/ecnivs/crank?style=flat-square">
  </a>
  <a href="https://github.com/ecnivs/crank/issues">
    <img src="https://img.shields.io/github/issues/ecnivs/crank?style=flat-square">
  </a>
  <a href="https://github.com/ecnivs/crank/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-Custom-blue?style=flat-square">
  </a>
  <img src="https://img.shields.io/github/languages/top/ecnivs/crank?style=flat-square">
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-informational?style=flat-square">
</p>

## Overview
Automate the creation of YouTube Shorts with customizable prompts, titles, tags, and descriptions. Designed for fast, efficient content generation while giving you full control over the output.

## 🛠️ Prerequisites
- Python 3.x (Tested with Python 3.13)
- Required Python libraries (listed in `requirements.txt`)
- `ffmpeg` and `ffprobe` installed and available in your system PATH (required for video processing)

#### Environment Variables
Crank uses a `.env` file to load sensitive keys and config values.
Make sure to create a `.env` file in the root directory containing your API keys, for example:
```ini
GEMINI_API_KEY=your_api_key_here
```

#### Credential Files
The other credentials are stored as JSON files inside the root directory:
- `secrets.json` — OAuth 2.0 client credentials JSON used for YouTube API upload authentication

## ⚙️ Customization
Crank is fully configurable. You can adjust prompts, descriptions, upload behavior, and other settings using your preffered method.

#### Default settings in `preset.yml`
Change the following directly in the file:
- `NAME`: the channel name
- `UPLOAD`: `true` or `false` to enable/disable uploads
- `DELAY`: number of hours between uploads: `0` for instant upload, or any positive number to schedule the video that many hours later.
- `DESCRIPTION`: default video description
- `TAGS`: list of tags for each video
- `CATEGORY_ID`: defines video category (defaults to `24`)
- `GEMINI_API_KEY`: optional channel-specific API key (overrides .env if set)
- `WHISPER_MODEL`: preferred whisper model (`tiny`, `base`, `small`, `medium`, `large-v1`, `large-v2`, `large-v3`; defaults to `small`)
- Prompt configurations (`CONTENT_PROMPT`, `GET_TITLE`, `TERM_PROMPT`): control how transcripts, titles, and subjects are generated.

## 📦 Installation
1. **Clone the repository**
```bash
git clone https://github.com/ecnivs/crank.git
cd crank
```
2. **Install dependencies**
```bash
pip install -r requirements.txt
```
3. **Install `ffmpeg`**
```bash
# Debian / Ubuntu
sudo apt install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

## 🚀 Running Crank
Run the tool with the default configuration:
```bash
python main.py
```
Or provide your custom config file with `--path`:
```bash
python main.py --path path/to/your_config.yml
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
