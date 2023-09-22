import { AppRunHistoryTimeline } from "../components/apps/AppRunHistoryTimeline";

export default function HistoryPage() {
  return (
    <div id="history-page">
      <AppRunHistoryTimeline showFilterBar={true} />
    </div>
  );
}
