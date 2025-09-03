import schedule from "node-schedule";

export async function initTaskScheduler({ intensity, calendar, timezone }) {
  const map = { low: "0 9 * * *", medium: "0 12 * * *", high: "0 15 * * *", max: "*/30 * * * *" };
  const rule = map[intensity] || map.max;
  schedule.scheduleJob(rule, () =>
    console.log("🔔 Reminder at", new Date().toLocaleString("en-US", { timeZone: timezone }))
  );
  console.log("TaskScheduler active with rule:", rule);
}
