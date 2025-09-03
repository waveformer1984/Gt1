# HydiGUI (Extended)

Includes:
- Live REPL
- Mood Engine
- Voice toggle (stubbed)
- Drag-and-drop chaining
- Auto-shell router (stubbed)
- TTS engine hook (stub)

Compile:
```
javac --module-path <path-to-javafx> --add-modules javafx.controls -d out src/hydi_gui/*.java
java --module-path <path-to-javafx> --add-modules javafx.controls -cp out hydi_gui.HydiGUI
```
