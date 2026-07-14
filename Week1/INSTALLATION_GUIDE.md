# Installation Guide – AI Workspace

## 1) Clone the Repository

```bash
git clone https://github.com/Abdullah-ML-ENG/AI-Agent-Fellowship-2026.git
cd AI-Agent-Fellowship-2026
```

## 2) Open the Project

Since this is a static frontend project, you can run it in two ways:

### Option A — Direct Open
Open `index.html` directly in your browser.

### Option B — Local Server (Recommended)
Run a local HTTP server for best browser compatibility:

```bash
python -m http.server 5500
```

Then open:
`http://localhost:5500`

## 3) Configure API Keys

Inside the app settings panel:

- Select provider: **Groq** or **Gemini**
- Enter corresponding API key
- Choose model
- Start chatting

> Keys are kept in browser session memory by the app logic.

## 4) First Login (Local Auth Screen)

On first run, create:

- Username
- Password

These are stored in browser local storage for local dashboard access.

## 5) Recommended Repository Files

Ensure the repo contains:

- `index.html`
- `README.md`
- `requirements.txt`
- `INSTALLATION_GUIDE.md`

## 6) Important Compatibility Notes

- Voice typing requires browser speech recognition support.
- Internet connection is required for:
  - Google Fonts
  - CDN scripts (`marked`, `dompurify`)
  - API provider requests (Groq/Gemini)

## 7) Troubleshooting

- **Authentication failed:** verify API key.
- **No model response:** check selected provider/model and internet connectivity.
- **Rate limit errors:** wait and retry.
- **Voice button unavailable:** browser does not support SpeechRecognition API.
