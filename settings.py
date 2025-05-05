import os
import re
import requests
import json
import logging
import time
import subprocess
import datetime
import glob
import random
import shutil
import tempfile
from pydub import AudioSegment
import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG, # Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                    format='%(levelname)s - %(message)s', # Define log message format
                    force=True) # Override existing logging settings

# -------------------------------
# Preferences
# -------------------------------
DEFAULT_VOICE = "speaker2"
DEFAULT_AUDIO = "piano"
DELAY = 60

# -------------------------------
# File Paths
# -------------------------------
SECRETS_JSON = "json/secrets.json"
KEY_JSON = "json/key.json"
FRAMES_DIR = "frames"

# -------------------------------
# Speech Processing Settings
# -------------------------------
TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2" # Text-to-speech model
SAMPLING_RATE = 16000 # Audio sampling rate (Hz)
CHUNK_SIZE = 1024 # Size of each audio chunk
FRAMES_PER_BUFFER = 4096 # Buffer size for audio processing
EXCEPTION_ON_OVERFLOW = False # Prevent exceptions on buffer overflow
RATE = SAMPLING_RATE # Audio rate (should match SAMPLING_RATE)

# -------------------------------
# LLM Configuration
# -------------------------------
ENDPOINT_1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
ENDPOINT_2 = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"

# -------------------------------
# Prompt Configuration
# -------------------------------
GET_TITLE = """
Given the following YouTube video content, generate a catchy, concise, and SEO-optimized title that would maximize clicks and accurately reflect the core idea of the video.
Avoid clickbait and keep it under 5 words.
Do not use any formatting and return only the title.
Do not include any filler, reactions or commentary.
"""

GET_INTRO = """
Read the following content and generate an engaging, attention-grabbing intro in under 10 words for a YouTube short.
The intro should spark curiosity, be concise, and create intrigue to encourage viewers to watch the entire short.
Use an attention-getting phrase like 'Did you know?' or 'Here’s something you probably didn’t know!' Adapt the tone to fit the subject matter (fun, mysterious, surprising, etc.).
Keep it short and impactful.
Do not include any questions, reactions or commentary.
Do not use any formatting and return only the intro.
"""

GET_DESCRIPTION = """
Generate a dynamic YouTube video description tailored to the content below. It should include:
- A short, engaging summary (1–2 sentences) that hooks viewers.
- Relevant keywords for SEO, woven naturally.
- A call-to-action encouraging likes, subs, or comments—written in a casual, human tone.
- Relevant hashtags clearly seperated.

Keep the tone conversational and viewer-friendly.
Avoid robotic language.
Make sure it flows naturally when read aloud.
Use plain punctuation—no excessive commas or semicolons.
Do not use any formatting and return only the description.
"""

GET_TAGS = """
Based on the following YouTube video content, generate a list of relevant, high-ranking SEO tags a total of 500 characters.
Output the tags only, separated by commas.
Do not include hashtags, explanations, or formatting—just raw tags.
"""

CONTENT_PROMPT = """
The flow must sound natural when read aloud by a TTS engine.
Avoid excessive commas, complex phrasing, and abrupt sentence breaks.
Each sentence must be clear, conversational, and under 20 words.
Keep punctuation minimal. Prioritize smooth rhythm over strict grammar.
The output should sound like natural spoken narration, not formal writing.
"""
