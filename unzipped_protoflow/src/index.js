import { scaffoldProjectEntry } from "./scaffolder.js";
import { validateEntry } from "./udpValidator.js";
import { initTaskScheduler } from "./taskScheduler.js";
import { startBLEGateway } from "./bluetoothHub.js";

async function runAll() {
  console.log("🚀 Starting ProtoFlow orchestrator...");

  await Promise.all([
    scaffoldProjectEntry(),
    validateEntry(),
    initTaskScheduler({ intensity: 'max', calendar: 'google', timezone: 'America/Chicago', lazy: false }),
    startBLEGateway(process.env.PHONE_NAME || "Felicia's Microwave"),
  ]);

  console.log("✅ All ProtoFlow modules are running in parallel.");
}

runAll();
