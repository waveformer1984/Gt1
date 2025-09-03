import { NobleBindings } from "@abandonware/noble";

export async function startBLEGateway(targetName) {
  const noble = new NobleBindings();
  noble.on("stateChange", s => (s === "poweredOn" ? noble.startScanning() : noble.stopScanning()));
  noble.on("discover", async p => {
    const name = p.advertisement.localName || "Unknown";
    if (name.includes(targetName)) {
      console.log("✅ Found", name, "—connecting…");
      noble.stopScanning();
      await connectToDevice(p);
    } else console.log("Found BLE device:", name);
  });
}

async function connectToDevice(p) {
  return new Promise((res, rej) => {
    p.connect(err => {
      if (err) return rej(err);
      console.log("🔌 Connected to", p.advertisement.localName);
      p.discoverAllServicesAndCharacteristics((e, svcs, chs) => {
        if (e) return rej(e);
        const notify = chs.find(c => c.properties.includes("notify"));
        if (notify) {
          notify.on("data", d => console.log("📲", d.toString("hex")));
          notify.subscribe(e2 => (e2 ? console.error(e2) : console.log("Subscribed")));
        }
        res();
      });
      p.on("disconnect", () => startBLEGateway(targetName));
    });
  });
}
