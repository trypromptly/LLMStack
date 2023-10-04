import { AppRunHistoryTimeline } from "../components/apps/AppRunHistoryTimeline";

export default function HistoryPage() {
  return (
    <div id="history-page" style={{ marginBottom: "60px" }}>
      <AppRunHistoryTimeline showFilterBar={true} />
    </div>
  );
}
