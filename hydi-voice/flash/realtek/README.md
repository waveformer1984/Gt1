# Realtek OTA (RTL8762/877x) — detection and next steps

Indicators:
- ManufacturerData company IDs observed in adverts often map to Realtek.
- Services/Characteristics resemble OTA control/data channels used by companion apps (e.g., DaFit clones).

Status:
- OTA protocol variants differ by vendor. Once we confirm UUIDs from the probe, we can provide a tailored Python BLE OTA client.

Prep:
- Keep watch awake and not bonded to phone.
- Obtain the correct OTA image (`.bin` or vendor‑specific package`).

Next steps (after probe output):
- We’ll map your watch’s OTA control/data UUIDs and provide exact flashing commands.
- If OTA requires an app menu, we’ll outline how to enter OTA mode on the watch.