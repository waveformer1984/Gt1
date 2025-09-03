
import os

CORE_DIRS = [
    "hydi_repl",
    "shell_router",
    "self_fix",
    "tts_translate",
    "command_scheduler",
    "context_memory"
]

EXPERIMENTS_DIR = "experiments"

def is_enabled(path):
    try:
        with open(path, "r") as f:
            return f.read().strip().lower() == "true"
    except FileNotFoundError:
        return False

def scan_and_activate():
    print("🧠 Scanning for enabled modules...")
    for module in CORE_DIRS:
        toggle_path = f"{module}__ENABLED__.toggle"
        if is_enabled(toggle_path):
            print(f"✅ Activating: {module}")
        else:
            print(f"⛔ Skipped (disabled): {module}")

    if os.path.isdir(EXPERIMENTS_DIR):
        for file in os.listdir(EXPERIMENTS_DIR):
            if file.endswith("__ENABLED__.toggle"):
                module = file.replace("__ENABLED__.toggle", "")
                path = os.path.join(EXPERIMENTS_DIR, file)
                if is_enabled(path):
                    print(f"⚗️  Experimental module ON: {module}")
                else:
                    print(f"🧪 Experimental module OFF: {module}")

if __name__ == "__main__":
    scan_and_activate()
