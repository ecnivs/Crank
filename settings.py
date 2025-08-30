import logging
from dotenv import load_dotenv
from contextlib import contextmanager
import shutil
import tempfile

load_dotenv()

# -------------------------------
# Temporary Workspace
# -------------------------------
@contextmanager
def new_workspace():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG, # Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                    format='%(levelname)s - %(message)s', # Define log message format
                    force=True) # Override existing logging settings

# -------------------------------
# Speech Configuration
# -------------------------------
VOICES = [
    'Zephyr',
    'Kore',
    'Orus',
    'Autonoe',
    'Umbriel',
    'Erinome',
    'Laomedeia',
    'Schedar',
    'Achird',
    'Sadachbia',
    'Puck',
    'Fenrir',
    'Aoede',
    'Enceladus',
    'Algieba',
    'Algenib',
    'Achernar',
    'Gacrux',
    'Zubenelgenubi',
    'Sadaltager',
    'Charon',
    'Leda',
    'Callirrhoe',
    'Iapetus',
    'Despina',
    'Rasalgethi',
    'Alnilam',
    'Pulcherrima',
    'Vindemiatrix',
    'Sulafat'
]

# -------------------------------
# Prompt Configuration
# -------------------------------
CONTENT_PROMPT = """
Create a YouTube SHORT transcript about Genshin Impact LORE focusing on "[TOPIC]".

LORE CONTENT TYPES TO COVER:
- Character backstories and hidden secrets
- Regional lore and geography mysteries  
- Artifact lore and their dark histories
- Weapon backstories and tragic origins
- Archon secrets and divine conflicts
- Ancient civilizations (Khaenri'ah, Enkanomiya, etc.)
- Hidden connections between characters
- Environmental storytelling details
- Book lore and in-game text secrets
- Mythology and real-world inspirations
- Timeline mysteries and plot twists
- Tragic character fates and sacrifices

FORMAT REQUIREMENT:
Write EXACTLY like this example format:
"Say enthusiastically: Did you know Zhongli is over 6000 years old?
Say mysteriously: But here's the secret most players missed.
Say excitedly: He actually created the very mora we use in the game!"

TRANSCRIPT STRUCTURE:
- 3-5 short sentences maximum (60 second limit)
- Each sentence starts with "Say [tone/emotion]:" followed by the lore content
- Use different tones for each sentence to create dynamic delivery
- End with an engagement prompt about the lore

TONE OPTIONS FOR LORE CONTENT:
- Say mysteriously: (for secrets and hidden lore)
- Say dramatically: (for tragic backstories)
- Say ominously: (for dark lore and curses)
- Say excitedly: (for surprising discoveries)
- Say conspiratorially: (for theories and connections)
- Say sadly: (for character tragedies)
- Say amazed: (for incredible revelations)
- Say eerily: (for creepy lore details)

LORE-SPECIFIC REQUIREMENTS:
- Reference specific in-game sources (artifacts, books, voice lines)
- Include character names, locations, and events accurately
- Reveal lesser-known facts most players miss
- Connect different pieces of Teyvat's history
- Build to a shocking lore revelation or dark truth
- End with lore-focused engagement ("What's your favorite dark theory?" "Did this lore shock you?")

Generate a complete lore-focused transcript following the "Say [tone]:" format that reveals fascinating Genshin Impact secrets and backstories.
Return only the transcript.
"""

TERM_PROMPT = """
Find a YouTube video search term for a Genshin Impact cinematic that matches the content:

The search term is the topic of discussion in a single word or two.
Example - Eula

Response Format:
Return ONLY a single short search term, nothing else. Example:
'Inazuma'

Fallback Rule:
If no video perfectly matches, return the closest / generic clean, high-quality Genshin Impact search term.

Content to match visually:
"""
