import { useState } from "react";
import { Box, Tabs, Tab } from "@mui/material";
import { AppRunHistorySessions } from "./AppRunHistorySessions";
import { AppRunHistoryTimeline } from "./AppRunHistoryTimeline";

export function AppRunHistory(props) {
  const { app } = props;
  const [selectedTab, setSelectedTab] = useState(0);
  const tabs = [
    {
      label: "Sessions",
      value: 0,
    },
    {
      label: "Timeline",
      value: 1,
    },
  ];

  return (
    <Box>
      <Tabs
        value={selectedTab}
        onChange={(e, newValue) => setSelectedTab(newValue)}
        sx={{
          borderBottom: "1px solid #ddd",
          mb: 2,
        }}
      >
        {tabs.map((tab) => (
          <Tab
            key={tab.value}
            label={tab.label}
            value={tab.value}
            sx={{ textTransform: "none" }}
          />
        ))}
      </Tabs>
      {selectedTab === 0 && <AppRunHistorySessions app={app} />}
      {selectedTab === 1 && (
        <AppRunHistoryTimeline
          filteredColumns={[
            "created_at",
            "request_user_email",
            "request_location",
            "response_time",
            "response_status",
          ]}
          filter={{ page: 1, app_uuid: app?.uuid }}
        />
      )}
    </Box>
  );
}
