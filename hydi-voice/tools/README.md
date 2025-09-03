# Watch Identification and Flashing Paths

1) Parse your MAC (from your note it is likely `72:3B:B0:82:03:2A`).

2) Scan and probe:
```bash
cd /workspace/hydi-voice
source .venv/bin/activate  # if not active
pip install -r requirements.txt
python3 tools/ble_probe.py --mac 72:3B:B0:82:03:2A --name "Z83"
```

3) Interpret results:
- ManufacturerData company ID hints chipset. Examples:
  - 0x0059 → Nordic (nRF52) → use Nordic DFU
  - 0x0171 → Realtek (RTL8762/877x) → Realtek OTA
  - 0x0211 or 0x066F → Telink → Telink OTA
  - 0x000D → TI → TI OAD
- DIS fields (Manufacturer/Model/FW) often include chipset clues.
- Service UUIDs:
  - FE59 → Nordic DFU
  - FEE7/FEE0 patterns → Xiaomi/Realtek variants

4) Next steps by chipset:
- nRF52 (Nordic DFU): build DFU zip and update via BLE.
- Realtek RTL8762: package OTA image and push via Realtek OTA (we can add tooling).
- Telink: use Telink OTA tool.
- Unknown/locked: use companion BLE bridge instead of flashing.

If you paste the probe output here, we’ll map it to the correct flashing method and generate exact commands.