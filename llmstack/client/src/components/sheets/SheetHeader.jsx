import React from "react";
import { Stack, Typography, Button, IconButton, Tooltip } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SaveIcon from "@mui/icons-material/Save";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import DownloadIcon from "@mui/icons-material/Download";
import { useNavigate } from "react-router-dom";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";

const SheetHeader = ({
  sheet,
  setRunId,
  hasChanges,
  onSave,
  sheetRunning,
  runId,
}) => {
  const navigate = useNavigate();

  const saveSheet = () => {
    onSave();
  };

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

  const downloadSheet = () => {
    window.open(`/api/sheets/${sheet.uuid}/download`, "_blank");
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
          <Stack direction={"row"} gap={1}>
            <Tooltip title="Save changes">
              <Button
                onClick={saveSheet}
                disabled={!hasChanges}
                color="primary"
                variant="outlined"
                sx={{ minWidth: "40px", padding: "5px", borderRadius: "4px" }}
              >
                <SaveIcon />
              </Button>
            </Tooltip>
            {!sheetRunning && (
              <Tooltip title="Download CSV">
                <Button
                  onClick={downloadSheet}
                  color="primary"
                  variant="outlined"
                  sx={{ minWidth: "40px", padding: "5px", borderRadius: "4px" }}
                >
                  <DownloadIcon />
                </Button>
              </Tooltip>
            )}
            <Tooltip
              title={
                sheetRunning ? "Sheet is already running" : "Run the sheet"
              }
            >
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
              </Button>
            </Tooltip>
          </Stack>
        </Stack>
      </Typography>
    </Stack>
  );
};

export default SheetHeader;
