#!/usr/bin/env python3
import asyncio
import argparse
from datetime import datetime
from bleak import BleakScanner


def parse_args():
    p = argparse.ArgumentParser(description="Log BLE adverts for a target device")
    p.add_argument("--mac", help="Target MAC address (optional)")
    p.add_argument("--name", help="Substring of device name to match (optional)")
    p.add_argument("--seconds", type=int, default=30, help="How long to log adverts")
    return p.parse_args()


def fmt_mfg(mfg: dict[int, bytes]) -> str:
    if not mfg:
        return "{}"
    parts = []
    for cid, data in mfg.items():
        parts.append(f"0x{cid:04X}:{data.hex()}")
    return "{" + ", ".join(parts) + "}"


async def main():
    args = parse_args()
    print(f"Logging BLE adverts for {args.seconds}s...")

    def cb(device, advertising_data):
        dn = device.name or ""
        da = device.address or ""
        if args.mac and da.lower() != args.mac.lower():
            return
        if args.name and args.name.lower() not in dn.lower():
            return
        ts = datetime.utcnow().isoformat()
        mfg = fmt_mfg(advertising_data.manufacturer_data or {})
        uuids = advertising_data.service_uuids or []
        rssi = device.rssi
        print(f"{ts} {da} {dn} RSSI={rssi} MFG={mfg} UUIDs={uuids}")

    scanner = BleakScanner(detection_callback=cb)
    await scanner.start()
    await asyncio.sleep(args.seconds)
    await scanner.stop()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())