## Hydi Voice (Local-first)

Quick voice UI using browser Speech Recognition (Chrome) and Speech Synthesis for replies. Backend is FastAPI with optional OpenAI integration.

### Features
- Hold-to-start style voice input (toggle button)
- Continuous mode and auto-speak options
- Simple bearer token gate via `HYDI_ACCESS_TOKEN`
- Optional OpenAI replies via `OPENAI_API_KEY`; else local echo reply

### Setup
1. Copy `.env.example` to `.env` and edit as needed:
   - Set `HYDI_ACCESS_TOKEN` to any secret (recommended)
   - Optionally set `OPENAI_API_KEY` for better replies
2. Create a Python virtual environment and install deps:
   ```bash
   cd /workspace/hydi-voice
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. Open the app in your browser:
   - `http://127.0.0.1:8000/`
   - Enter your access token (if set), click Save Token
   - Click Start Talking

### Notes
- Speech Recognition uses the browser API. For best results, use Chrome on desktop. Firefox does not support it. Edge may work.
- Speech Synthesis also uses the browser API and runs locally on your machine.
- To keep it private, do not expose the port publicly. Bind to `127.0.0.1` only.
- If you need offline STT (instead of browser API), we can integrate `faster-whisper` in the backend later.