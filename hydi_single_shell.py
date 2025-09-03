import os
import subprocess

try:
    import readline
except ImportError:
    import pyreadline as readline

print("Hydi Single-Shell REPL Started (v1.0)")
print("Type 'exit' to quit.\n")

while True:
    try:
        cmd = input("Hydi > ")
        if cmd.strip().lower() in ["exit", "quit"]:
            print("Goodbye.")
            break
        if cmd:
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(output.stdout or output.stderr)
    except KeyboardInterrupt:
        print("\n^C received, exiting.")
        break
    except Exception as e:
        print(f"?? Error: {e}")
