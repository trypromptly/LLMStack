import DownloadIcon from "@mui/icons-material/Download";
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Select,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { DateTimePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import moment from "moment";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import { profileFlagsSelector } from "../../data/atoms";
import { axios } from "../../data/axios";
import { AppRunHistorySessions } from "./AppRunHistorySessions";
import { AppRunHistoryTimeline } from "./AppRunHistoryTimeline";

const RunHistoryDownloadModal = ({ open, setOpen, appUuid }) => {
  const [beforeDateTime, setBeforeDateTime] = useState(moment());
  const [historyCount, setHistoryCount] = useState(25);
  const [brief, setBrief] = useState(true);

  return (
    <Dialog open={open} onClose={() => setOpen(false)}>
      <DialogTitle>Download History</DialogTitle>
      <DialogContent>
        Last{" "}
        <Select
          value={historyCount}
          variant="standard"
          onChange={(e) => setHistoryCount(e.target.value)}
        >
          <MenuItem value={25}>25</MenuItem>
          <MenuItem value={50}>50</MenuItem>
          <MenuItem value={100}>100</MenuItem>
        </Select>{" "}
        items <br />
        <br />
        <LocalizationProvider dateAdapter={AdapterMoment}>
          <DateTimePicker
            label="Before"
            value={beforeDateTime}
            onChange={(newValue) => setBeforeDateTime(newValue)}
          />
        </LocalizationProvider>
        <br />
        <br />
        <Typography>
          <Checkbox
            label="Brief"
            checked={brief}
            onChange={(e) => setBrief(e.target.checked)}
          />
          Only include brief history (input, output and session info)
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button
          sx={{
            textTransform: "none",
          }}
          onClick={() => setOpen(false)}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          sx={{
            textTransform: "none",
          }}
          onClick={() => {
            axios()
              .post(
                `/api/history/download`,
                {
                  app_uuid: appUuid,
                  before: beforeDateTime,
                  count: historyCount,
                  brief: brief,
                },
                {
                  responseType: "blob",
                },
              )
              .then((response) => {
                const url = window.URL.createObjectURL(
                  new Blob([response.data]),
                );
                const link = document.createElement("a");
                link.href = url;
                link.setAttribute(
                  "download",
                  `history_${appUuid}_${moment(beforeDateTime).format(
                    "MM:DD:YYYY_HH:MM:SS_s",
                  )}_${historyCount}.csv`,
                );
                document.body.appendChild(link);
                link.click();
              })
              .catch((error) => {
                enqueueSnackbar("Error downloading history", {
                  variant: "error",
                });
                console.error(error);
              })
              .finally(() => {
                setOpen(false);
              });
          }}
          autoFocus
        >
          Download CSV
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export function AppRunHistory(props) {
  const { app } = props;
  const [selectedTab, setSelectedTab] = useState(0);
  const [openDownloadModal, setOpenDownloadModal] = useState(false);
  const profileFlags = useRecoilValue(profileFlagsSelector);
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
      <Box sx={{ display: "flex", width: "100%", justifyContent: "end" }}></Box>
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
        <Button
          disabled={profileFlags?.CAN_EXPORT_HISTORY !== true}
          onClick={() => {
            setOpenDownloadModal(true);
          }}
          sx={{ textTransform: "none", ml: "auto" }}
          startIcon={<DownloadIcon />}
        >
          Download as CSV
        </Button>
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
      <RunHistoryDownloadModal
        open={openDownloadModal}
        setOpen={setOpenDownloadModal}
        appUuid={app?.uuid}
      />
    </Box>
  );
}
