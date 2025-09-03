# Flashing Prep: Z83 Max

Use this checklist before flashing. We will pick the correct method after identifying the chipset.

## 1) Power and safety
- Charge the watch to at least 70%.
- Keep the charger connected during flashing if possible.
- Use a stable PC/laptop power source (avoid battery drain or sleep).

## 2) Unpair and isolate
- Temporarily unpair the watch from any phone apps (so BLE stays available for DFU/OTA).
- Keep the watch screen awake and near the PC (within 0.5–1m).

## 3) Identify chipset and DFU/OTA method
Run the probe from your PC:
```bash
cd /workspace/hydi-voice
source .venv/bin/activate
pip install -r requirements.txt
python3 tools/ble_probe.py --mac 72:3B:B0:82:03:2A --name "Z83"
```
If needed, log adverts for a bit longer (30s):
```bash
python3 tools/ble_scan_log.py --mac 72:3B:B0:82:03:2A --name "Z83" --seconds 30
```

Interpret:
- ManufacturerData company ID and service UUIDs indicate the path:
  - FE59 present → Nordic Secure DFU (nRF52)
  - Realtek/Telink company IDs → Realtek/Telink OTA
  - None/unknown → likely locked; we use companion bridge (no OS flash)

## 4) Backup identifiers
- Record output from the probe (manufacturer, model, firmware rev, services, ManufacturerData).
- Take photos/screens of current firmware/version screens on the watch UI.

## 5) Firmware image
- Obtain the correct firmware (Hydi build) for your chipset and version.
- Verify checksum/signature if provided.
- Note: reading firmware back from many BLE watches is not possible; ensure the image is correct.

## 6) Environment tools (install what applies after identification)
- Nordic DFU: `pip install nrfutil` (or `pip install nordicsemi`) and have Bluetooth enabled.
- Realtek/Telink: tooling depends on variant; we’ll add the right utility after detection.

## 7) Flashing mode
- Nordic: the app usually exposes Buttonless DFU; we will trigger DFU over BLE.
- Realtek/Telink: watch may need to enter OTA mode from a hidden menu/app.

## 8) Post-flash
- Do not move the watch away until it reboots fully.
- Verify version and basic functions.
- Re‑pair with your phone or with Hydi’s bridge.