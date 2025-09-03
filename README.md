# 🍑 ballsDeepnit – The Deepest, Most Savage Bot Framework in the Game

![Hydra Logo](https://user-images.githubusercontent.com/00000000/placeholder.png)  
*“Go deep or go home.” – main dame, ballsDeepnit founder*

---

## 🚀 Overview

**ballsDeepnit** is a modular Python automation platform for real ones only.  
Hot-reload plugins, rule your bots from a web dashboard, and trigger *anything* with MIDI, voice, or your dirty imagination.  
You want it automated?  
You’d better be ready to go balls deep.

---

## 📦 Features

- **Hot Reload:** Change plugins on the fly. Don’t even think about restarting.
- **Web Dashboard:** Point, click, run, flex.
- **Meta-Bot Plugin Generator:** Scaffold new bots with one command or from the dashboard.
- **Voice & MIDI Triggers:** Speak it or play it, your bots obey.
- **Parallel/Sandbox Execution:** Every plugin has its own little padded room.
- **Device Bots:** Synths, 3D printers, MPC, future toys, you name it.
- **Notifications:** Discord/webhook/email alerts for bot drama.
- **Sass, Style, and Jokes:** Docs so good they’re probably NSFW.

---

## 💻 Requirements

- **Python 3.10+**
- **pip** or **poetry**
- **Git** (version control, for real devs)
- **Node.js** *(only for fancy frontend work, not required for backend/plugins)*

### **Python Dependencies**
See `pyproject.toml`:
- Flask
- watchdog
- python-rtmidi
- sounddevice
- SpeechRecognition
- multiprocess
- discord-webhook
- pyserial
- requests
- python-dotenv

---

## 🔥 Quickstart

```sh
git clone https://github.com/Waveformer1984/ballsDeepnit.git
cd ballsDeepnit

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
# OR (recommended)
poetry install

cp .env.example .env
# Edit .env with your secrets

python main.py           # Launch the core
python dashboard/dashboard.py   # Open the dashboard

python scripts/plugin_scaffold.py your_plugin_name   # Scaffold a new plugin
# Register it in pyproject.toml under [project.entry-points.'hydra.plugins']
# your_plugin_name = "plugins.your_plugin_name:YourPluginName"
