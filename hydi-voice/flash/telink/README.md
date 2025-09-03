# Telink OTA — detection and approach

Indicators:
- Company IDs like 0x0211/0x066F; service UUID patterns typical of Telink.

Approach:
- Use Telink OTA GATT service to send the image.
- Requires the correct image format and version headers.

Next steps:
- After probe confirms Telink, we’ll add a scripted OTA client and exact commands here.