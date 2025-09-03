This folder stores Cursor artifacts.

- process-artifact-data-f408: add the actual artifact content here if needed.

## process_artifact_data_f408.py
Generate an artifact JSON of repository files:

```bash
python3 cursor/process_artifact_data_f408.py --base-dir .
# Output: cursor/process-artifact-data-f408.json
```

Options:
- `--base-dir DIR`: directory to scan (default: `.`)
- `--output PATH`: explicit output path
- `--max-preview-bytes N`: include up to N bytes of small text files as preview
