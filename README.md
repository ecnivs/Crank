# Crank
> Youtube Shorts Generator

![IMG_20250901_182631](https://github.com/user-attachments/assets/2c272049-acc0-4b50-9b69-67c71cadf07e)



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

#### Default settings in `config.yml`
Change the following directly in the file:
- `NAME`: the channel name
- `UPLOAD`: `true` or `false` to enable/disable uploads
- `DESCRIPTION`: default video description
- `TAGS`: list of tags for each video
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
sudo apt install ffmpeg  # debian

# Arch Linux
sudo pacman -S ffmpeg  # arch

# macOS (Homebrew)
brew install ffmpeg  # macos

# Windows (using Chocolatey)
choco install ffmpeg  # windows
```

## 🚀 Runing Crank
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
<a href='https://ko-fi.com/U6U113P6OM' target='_blank'><img height='60' style='border:0px;width:217px;' src='https://storage.ko-fi.com/cdn/kofi3.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
</div>

## 🙌 Contributing
We appreciate any feedback or code reviews! Feel free to:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Submit a pull request

### I'd appreciate any feedback or code reviews you might have!
