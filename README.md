# EE471 — Week 5: Speech-Studio & Voice-Activated Calculator

**Course:** EE471 Modern Software Development Practices and Technologies  
**Institution:** Izmir Institute of Technology — Electrical & Electronics Eng. Dep.  
**Date:** 26/10/2026  

---

## Repository Structure

```
EE471-week5/
├── .env.example              # Template for Azure Speech credentials
├── .gitignore                # Protects secret keys (.env) and cache
├── requirements.txt          # Python dependencies
├── PROMPTS.md                # Vibe coding prompts & transcript log
│
├── Week-5-Task-1/            # Speech Services Studio
│   ├── app.py                # Flask server (TTS & STT routes)
│   ├── templates/index.html  # Unified tabbed interface
│   └── static/
│       ├── style.css         # Modern Azure Speech Services design
│       └── script.js         # Audio recording, PCM WAV encoder, player
│
└── Week-5-Task-2/            # Voice-Activated Smart Calculator
    ├── app.py                # Safe calculation & voice command parser
    ├── templates/index.html  # Blue chassis calculator with left mic button
    └── static/
        ├── style.css         # Styling matching PDF page 3
        └── script.js         # Voice recognition + speaking buttons
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Task 1 (Speech Studio)
```bash
cd Week-5-Task-1
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 3. Run Task 2 (Voice-Activated Calculator)
```bash
cd Week-5-Task-2
python app.py
```
Open [http://127.0.0.1:5002](http://127.0.0.1:5002)
