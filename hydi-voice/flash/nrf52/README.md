# Nordic nRF52 Secure DFU (if FE59 present)

Prereqs:
```bash
pip install --upgrade pip
pip install nrfutil  # or: pip install nordicsemi
```

Prepare DFU package (zip must contain app.bin + app.dat with correct signatures):
```bash
# Example; replace with your actual DFU package
ls hydi_app_dfu.zip
```

Trigger DFU over BLE (by name or MAC):
```bash
# By name
nrfutil dfu ble -pkg hydi_app_dfu.zip -n "Z83" --conn-interval 20,75 --ic NRF52

# Or by MAC (Linux BlueZ address)
nrfutil dfu ble -pkg hydi_app_dfu.zip -a 72:3B:B0:82:03:2A --conn-interval 20,75 --ic NRF52
```

Notes:
- If the device doesn’t expose FE59, DFU is not available; identify another method.
- Keep the watch close; DFU can take several minutes.
- If DFU fails mid‑way, power‑cycle the watch and retry.