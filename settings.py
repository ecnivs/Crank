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
import asyncio

load_dotenv()

class OnCooldown(Exception):
    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0] if self.args else ''}"

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
DELAY = 10

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
# API Urls
# -------------------------------
ENDPOINT_1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
ENDPOINT_2 = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
PIXABAY_URL = "https://pixabay.com/api/videos/"

# -------------------------------
# Prompt Configuration
# -------------------------------
GET_TITLE = """
Given the following YouTube video content, generate a catchy, concise, and SEO-optimized title that would maximize clicks and accurately reflect the core idea of the video.
- Keep it under 5 words.
- No clickbait or exaggeration.
- No formatting.
- Output only the title — no filler, no commentary, no reactions.
- Avoid terms that may violate YouTube's community guidelines such as 'suicide', 'violence', 'abuse', or any other harmful or sensitive terms.
"""

GET_INTRO = """
Read the content and create a powerful, curiosity-sparking intro in under 10 words for a YouTube Short.
The intro should imply a reveal, mystery, or hidden truth.
Avoid questions, reactions, or commentary.
Use an attention-grabbing phrase like 'Here’s something you probably didn’t know' or 'You won’t believe this fact.'
Make it feel like the viewer needs to keep watching to understand.
Return only the raw intro text — no formatting.
"""

GET_SEARCH_TAGS = """
Write short, catchy Pixabay video search tags (under 3 words) that visually represent the scene, theme, or emotion of the content below.
Rules:
- Focus on visually satisfying, mesmerizing or attention-grabbing elements.
- Avoid tags that would show visible faces (hands, silhouettes, or body parts are okay)
- Prioritize tags that return visually captivating, loop-worthy footage.
- Use only simple, broad visual terms that return relevant videos on Pixabay.
- If there is a direct visual subject, name only that subject (e.g., "Eiffel Tower").
- Do not add modifiers, adjectives, or extra descriptive words that don’t clearly identify a visual element.
- No explanations or extra text. Return only raw tags separated by commas.
"""

GET_DESCRIPTION = """
Write a short YouTube description for a video based on a fictional or anonymous story.
Requirements:
- A 1–2 sentence hook that captures the emotional or thematic core of the content (not the video structure).
- Embed source and if needed date in a natural narrative way using phrases like "According to" or "As recorded in".
- Include SEO-relevant keywords woven into natural language.
- Add a casual, human call-to-action encouraging likes, comments, or subscriptions.
- End with exactly 15 space-separated relevant hashtags (no commas).

Strict Rules:
- Avoid terms that may violate YouTube's community guidelines such as 'suicide', 'violence', 'abuse', or any other harmful or sensitive terms.
- Use a natural, viewer-friendly tone. No robotic, corporate, or formal phrasing.
- Ensure it reads smoothly when spoken aloud.
- Use simple punctuation. No formatting or list markers.
- Output only the raw description.
"""

GET_TAGS = """
Generate a comma-separated list of SEO-friendly YouTube tags based on the following video content.
Requirements:
- Output only the tags. No hashtags, no explanations, no formatting.
- Each tag must be a single string with no more than 30 characters.
- No special characters such as <, >, ", #, or newlines.
- Avoid terms that may violate YouTube's community guidelines such as 'suicide', 'violence', 'abuse', or any other harmful or sensitive terms.
- Limit to 30 tags maximum.
- Total combined length of all tags, including commas, must not exceed 500 characters.
Return only the tags, separated by commas.
"""

CONTENT_PROMPT = """
Given the following description, generate content for a YouTube short.
Rules:
- Keep the response short, clear, and natural.
- Max 175 words, but use fewer if possible.
- The flow must sound natural when read aloud by a TTS engine.
- Avoid excessive commas, complex phrasing, and abrupt sentence breaks.
- Each sentence must be clear, concise, conversational, and under 15 words but fewer if possible.
- Keep punctuation minimal. Prioritize smooth rhythm over strict grammar.
- The output should sound like natural spoken narration, not formal writing.
- Ensure that any information returned is accurate and upto date.
- Be direct, vivid, and engaging.
- No introductions or fillers needed. No commentary, questions, or reactions.
- Include surprising detail that will grab viewers' attention.
- Embed source and if needed date in a natural narrative way using phrases like "According to" or "As recorded in".
- If your response is based on older data clearly label it as such and flag any parts that might be outdated or disproved.
"""

DISCLAIMER = """
Disclaimer: This content was generated by Gemini and may include creative interpretations not present in the official sources.
It is intended for entertainment purposes.
"""
