# -------------------------------
# Video Configuration
# -------------------------------
DESCRIPTION = """
#genshinimpact #genshinlore #teyvat #genshinshorts #genshinstory #lore #genshin #genshin_impact #genshinedit #genshinimpactedit #genshinimpactlore #genshinfandom 
#genshinimpactgameplay #genshinshort #genshingameplay
"""

TAGS = [
    "Genshin Impact", "Genshin Impact 2025", "miHoYo", "open world RPG", "action RPG",
    "anime game", "Teyvat lore", "Genshin Impact characters", "Ganyu", "Zhongli",
    "Venti", "Raiden Shogun", "elemental reactions", "gameplay", "guide",
    "tips and tricks", "montage", "cinematic", "story walkthrough", "new update"
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

GET_TITLE = """
Given the following YouTube video content, generate a catchy, concise, and SEO-optimized title that would maximize clicks and accurately reflect the core idea of the video.
- Keep it under 5 words.
- No clickbait or exaggeration.
- No formatting.
- Output only the title: no filler, no commentary, no reactions.
- Avoid terms that may violate YouTube's community guidelines such as 'suicide', 'violence', 'abuse', or any other harmful or sensitive terms.
"""

TERM_PROMPT = """
Given the content below, identify the main subject discussed.

- The subject will always be an entity from Genshin Impact.
- Return ONLY a single word or short phrase representing that subject.
- Do NOT include any explanation, punctuation, quotes, or extra text.
- Examples: Eula, Inazuma, Ganyu, Skyward Blade

OUTPUT FORMAT REQUIREMENT:
Genshin Impact Cinematic {Subject}

Content to analyze:
"""
