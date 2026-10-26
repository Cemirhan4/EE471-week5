# Vibe Coding Transcripts & Prompts Log (Week #5)

**Course:** EE471 Modern Software Development Practices and Technologies  
**Assignment:** In-class exercise Week #5 — Speech Services & Voice-Activated Calculator  
**Student:** Cemirhan  

---

## Task 1: Speech-Studio-Backed Website

### Prompt 1 (Part 0 & 1: Initial Setup and Text-to-Speech)
> *"Create a Flask-based website for Week-5-Task-1 with a Text-to-Speech feature. It should use Azure Speech Services SDK with a .env file for SPEECH_KEY and SPEECH_REGION, plus a local fallback so it works without external keys. Design the UI matching the course handout with a text input, 'Synthesize Speech' button, audio player, and download button."*

### Prompt 2 (Part 2: Speech-to-Text)
> *"Develop the Speech-to-Text branch. Users should be able to record audio with their microphone or upload a file, transcribe it to text, view the transcription, and copy the text."*

### Prompt 3 (Part 3: Merge Conflicts & Multi-Tab App)
> *"Simulate a merge conflict between the text-to-speech and speech-to-text branches. Resolve the conflict by unifying both features into a clean tabbed UI matching the Azure Speech Services screenshot."*

### Manual Corrections & Fixes Made (Task 1):
1. **Audio Format Codec Mismatch:**
   - *Problem:* Standard browser `MediaRecorder` generates compressed WebM/Opus audio. Python's wave and speech recognition libraries failed with `Audio file could not be read as PCM WAV`.
   - *Fix:* Implemented a native 16-bit PCM WAV encoder in pure JavaScript using the Web Audio API (`AudioContext`). It samples the microphone at 16,000 Hz Mono and encodes a real uncompressed RIFF WAV, allowing immediate recognition in Python without external `ffmpeg` dependencies.
2. **Audio Caching on Re-synthesis:**
   - *Problem:* Browsers cached the generated audio file (`synthesized_speech.wav`), causing old audio to play when new text was synthesized.
   - *Fix:* Added a timestamp query parameter (`?t=timestamp`) to the audio URL to force the browser to reload newly synthesized audio.

---

## Task 2: Voice-Activated & Speaking Smart Calculator

### Prompt 1 (Voice Calculator Architecture)
> *"Build Week-5-Task-2: A voice-activated smart calculator in Flask. The UI must match the assignment diagram with a vertical microphone button on the left of the keypad. It should execute voice commands according to the command table ('Zero' to 'Nine', 'Point' for '.', 'Over' for '÷', 'Times' for 'x', 'Plus' for '+', 'Minus' for '-', 'Is' for '=')."*

### Prompt 2 (Magical Speaking Buttons)
> *"Make the manual buttons speak out loud when pressed (e.g. clicking 3, +, 5, = speaks 'Three', 'plus', 'five', 'is eight'). Implement safe backend calculation in Flask without eval()."*

### Manual Corrections & Fixes Made (Task 2):
1. **Natural Language Normalization:**
   - *Problem:* Speech recognition often introduces commas or capitalization (e.g., `"Five, plus, two, is"`).
   - *Fix:* Added robust string normalization in `/api/voice-command` that strips punctuation, maps synonyms (e.g., `'divided by'` or `'over'` to `'/'`, `'times'` or `'multiplied by'` to `'*'`), and parses tokens into operands and operators safely.
2. **Instant Audio Response for Buttons:**
   - *Problem:* Calling a remote TTS endpoint on every button click created a 500ms network lag before the number was spoken.
   - *Fix:* Used the Web Speech API (`SpeechSynthesis`) with `window.speechSynthesis.cancel()` on button clicks for immediate, zero-latency speech feedback, keeping calculation execution strictly on the Flask backend.
