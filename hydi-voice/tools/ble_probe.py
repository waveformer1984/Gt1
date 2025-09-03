#!/usr/bin/env python3
import asyncio
import argparse
from typing import Optional

from bleak import BleakClient, BleakScanner

# DIS characteristic UUIDs
UUID_MANUFACTURER = "00002a29-0000-1000-8000-00805f9b34fb"
UUID_MODEL = "00002a24-0000-1000-8000-00805f9b34fb"
UUID_FWREV = "00002a26-0000-1000-8000-00805f9b34fb"
UUID_DIS_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"


def parse_args():
    p = argparse.ArgumentParser(description="Probe a BLE watch to identify chipset and DFU path")
    p.add_argument("--mac", help="Target MAC address (e.g., 72:3B:B0:82:03:2A)")
    p.add_argument("--name", help="Target device name to match (e.g., Z83 Max)")
    p.add_argument("--timeout", type=float, default=10.0, help="Scan timeout seconds")
    return p.parse_args()


def fmt_mfg(mfg: dict[int, bytes]) -> str:
    if not mfg:
        return "{}"
    parts: list[str] = []
    for cid, data in mfg.items():
        parts.append(f"0x{cid:04X}:{data.hex()}")
    return "{" + ", ".join(parts) + "}"


async def discover_target(name: Optional[str], mac: Optional[str], timeout: float):
    print(f"Scanning for {timeout}s...")
    devices = await BleakScanner.discover(timeout=timeout)
    target = None
    for d in devices:
        dn = d.name or ""
        da = d.address or ""
        if mac and da.lower() == mac.lower():
            target = d
            break
        if name and name.lower() in dn.lower():
            target = d
            break
    print(f"Found {len(devices)} devices.")
    if target is None:
        for d in devices:
            print(f"- {d.address} {d.name} RSSI={getattr(d, 'rssi', None)} MFG={fmt_mfg(d.metadata.get('manufacturer_data', {}))}")
        return None

    print(f"Target: {target.address} {target.name} RSSI={getattr(target, 'rssi', None)}")
    print(f"ManufacturerData: {fmt_mfg(target.metadata.get('manufacturer_data', {}))}")
    print(f"Advertised UUIDs: {target.metadata.get('uuids')}")
    return target


async def read_dis(client: BleakClient):
    out = {}
    try:
        data = await client.read_gatt_char(UUID_MANUFACTURER)
        out["manufacturer"] = data.decode(errors="ignore").strip()
    except Exception:
        pass
    try:
        data = await client.read_gatt_char(UUID_MODEL)
        out["model"] = data.decode(errors="ignore").strip()
    except Exception:
        pass
    try:
        data = await client.read_gatt_char(UUID_FWREV)
        out["firmware_rev"] = data.decode(errors="ignore").strip()
    except Exception:
        pass
    return out


async def main():
    args = parse_args()
    target = await discover_target(args.name, args.mac, args.timeout)
    if target is None:
        print("No matching device found.")
        return 2

    async with BleakClient(target.address) as client:
        print("Connected.")
        await client.get_services()
        has_dis = any(s.uuid.lower() == UUID_DIS_SERVICE for s in client.services)
        print(f"Has DIS: {has_dis}")
        info = await read_dis(client)
        print(f"DIS: {info}")
        print("Services:")
        for s in client.services:
            print(f"- {s.uuid} ({s.description})")
            # Heuristic hints
            ul = s.uuid.lower()
            if "f000ffc0-0451-4000-b000-000000000000" in ul:
                print("  hint: TI OAD present")
            if ul.startswith("0000fe59-"):
                print("  hint: Nordic DFU (buttonless)")
            if ul.startswith("0000fe5b-"):
                print("  hint: Garmin/ANT")
        print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))