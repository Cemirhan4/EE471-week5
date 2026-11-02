# EE471 — Week 5 & Week 6: Speech Services, Voice Calculator & Containerization (Docker & Cog)

**Course:** EE471 Modern Software Development Practices and Technologies  
**Institution:** Izmir Institute of Technology — Electrical & Electronics Eng. Dep.  

---

## 📂 Repository Structure

```
EE471-week5/
├── .env.example              # Template for Azure Speech credentials
├── .gitignore                # Protects secret keys (.env) and audio caches
├── docker-compose.yml        # Docker Compose configuration for Task 1 & Task 2
├── requirements.txt          # Python dependencies
├── PROMPTS.md                # Vibe coding prompts & transcript log
│
├── Week-5-Task-1/            # Speech Services Studio
│   ├── Dockerfile            # Container definition (Python 3.11-slim + audio libraries)
│   ├── requirements.txt      # Task-specific dependencies
│   ├── app.py                # Flask server (TTS & STT routes)
│   ├── templates/index.html  # Unified tabbed interface
│   └── static/
│       ├── style.css         # Modern Azure Speech Services design
│       └── script.js         # Audio recording, PCM WAV encoder, player
│
├── Week-5-Task-2/            # Voice-Activated Smart Calculator
│   ├── Dockerfile            # Container definition for Voice Calculator
│   ├── requirements.txt      # Task-specific dependencies
│   ├── app.py                # Safe calculation & voice command parser
│   ├── templates/index.html  # Blue chassis calculator with left mic button
│   └── static/
│       ├── style.css         # Styling matching assignment design
│       └── script.js         # Voice recognition + speaking buttons
│
└── Week-6-Task-2/            # Cog Machine Learning & Cat Kind Classifier
    ├── cog.yaml              # Cog container configuration (Python 3.11, PyTorch CPU)
    ├── predict.py            # Pre-trained ResNet-50 vision classifier
    ├── app.py                # Flask web interface connecting to Cog container
    ├── requirements.txt      # Cog dependencies
    ├── requirements-web.txt  # Web app dependencies
    ├── input.jpg             # Test cat sample image
    ├── templates/index.html  # Glassmorphic drag-and-drop web UI
    └── static/
        ├── style.css         # Modern dark theme with progress bars
        └── script.js         # Upload handler & live prediction visualizer
```

---

## 🐳 Docker Containerization (Week 6 - Task 1)

Both Week 5 applications are fully containerized using **Docker** and orchestrated via **Docker Compose**:

### Run both containers simultaneously:
```bash
docker compose up --build
```

- **Speech Studio:** [http://localhost:5000](http://localhost:5000)
- **Voice Calculator:** [http://localhost:5002](http://localhost:5002)

---

## 🐱 Cog Machine Learning & Cat Classifier (Week 6 - Task 2)

Packaged with **Replicate Cog** using a pre-trained **ResNet-50** vision model to classify cat breeds (*tiger cat, tabby, Egyptian cat, etc.*).

### 1. Test Prediction via Cog CLI (WSL):
```bash
cd Week-6-Task-2
cog run -i image=@input.jpg
```

### 2. Build and Run Standalone Cog Docker Container:
```bash
cog build -t cat-classifier
docker run -d -p 5001:5000 --name cat-cog cat-classifier
```

### 3. API Verification (Postman / cURL):
Send a POST request to the Cog inference endpoint:
```bash
curl -X POST http://localhost:5001/predictions \
  -H "Content-Type: application/json" \
  -d '{"input": {"image": "https://gist.githubusercontent.com/bfirsh/3c2115692682ae260932a67d93fd94a8/raw/56b19f53f7643bb6c0b822c410c366c3a6244de2/mystery.jpg"}}'
```

### 4. Run the Cat Classifier Web Interface:
```bash
cd Week-6-Task-2
pip install requests
python app.py
```
Open [http://localhost:5005](http://localhost:5005) in your browser.
