# Crank
> Youtube Shorts Generator

## Overview
This repo is dedicated to showcasing the automation of YouTube Shorts for my channel [Ask Irminsul](https://www.youtube.com/@askirminsul). It’s actively used and maintained to generate content efficiently.

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

## ⚙️ Installation
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
```bash
python main.py
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
