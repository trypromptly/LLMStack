import React from "react";
import { Stack, Typography, Button, IconButton, Tooltip } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import { useNavigate } from "react-router-dom";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";
import SettingsIcon from "@mui/icons-material/Settings";

const SheetHeader = ({
  sheet,
  setRunId,
  hasChanges,
  onSave,
  sheetRunning,
  runId,
}) => {
  const navigate = useNavigate();

  const runSheet = () => {
    const runSheetAction = () => {
      axios()
        .post(`/api/sheets/${sheet.uuid}/run`)
        .then((response) => {
          setRunId(response.data.run_id);
        })
        .catch((error) => {
          console.error(error);
          enqueueSnackbar(
            `Error running sheet: ${
              error?.response?.data?.detail || error.message
            }`,
            { variant: "error" },
          );
        });
    };

    if (hasChanges) {
      onSave().then(runSheetAction);
    } else {
      runSheetAction();
    }
  };

  return (
    <Stack>
      <Typography variant="h5" className="section-header">
        <Stack
          direction={"row"}
          sx={{ justifyContent: "space-between", alignItems: "center" }}
        >
          <Stack direction="row" alignItems="center" spacing={2}>
            <Tooltip title="Back to Sheets List">
              <IconButton
                onClick={() => navigate("/sheets")}
                sx={{ color: "action.disabled", padding: 0 }}
              >
                <ArrowBackIcon
                  fontSize="small"
                  sx={{
                    color: "action.disabled",
                    padding: 0,
                  }}
                />
              </IconButton>
            </Tooltip>
            <Stack>
              {sheet?.name}
              <Typography variant="caption" sx={{ color: "#666" }}>
                {sheet?.description || sheet?.data?.description || ""}
              </Typography>
            </Stack>
          </Stack>
          <Stack direction={"row"} gap={1} sx={{ marginRight: "-8px" }}>
            <Tooltip title={"Settings"}>
              <span>
                <Button
                  variant="contained"
                  size="medium"
                  onClick={() => {}}
                  disabled={sheetRunning}
                  sx={{
                    bgcolor: "gray.main",
                    "&:hover": { bgcolor: "gray.main" },
                    color: "#999",
                    minWidth: "40px",
                    padding: "5px",
                    borderRadius: "4px !important",
                  }}
                >
                  <SettingsIcon />
                </Button>
              </span>
            </Tooltip>
            <Tooltip
              title={
                sheetRunning ? "Sheet is already running" : "Run the sheet"
              }
            >
              <span>
                <Button
                  variant="contained"
                  size="medium"
                  onClick={runSheet}
                  disabled={sheetRunning}
                  sx={{
                    bgcolor: "success.main",
                    "&:hover": { bgcolor: "success.dark" },
                    minWidth: "40px",
                    padding: "5px",
                    borderRadius: "4px !important",
                  }}
                >
                  {sheetRunning ? <PauseIcon /> : <PlayArrowIcon />}
                  {sheetRunning ? "Pause" : "Execute"}
                </Button>
              </span>
            </Tooltip>
          </Stack>
        </Stack>
      </Typography>
    </Stack>
  );
};

export default SheetHeader;
