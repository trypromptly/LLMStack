import React, { useState } from "react";
import {
  Stack,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Popper,
  Paper,
  MenuList,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText,
  ClickAwayListener,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import SettingsIcon from "@mui/icons-material/Settings";
import DeleteIcon from "@mui/icons-material/Delete";
import HistoryIcon from "@mui/icons-material/History";
import AutorenewIcon from "@mui/icons-material/Autorenew";
import { useNavigate } from "react-router-dom";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";
import PreviousRunsModal from "./PreviousRunsModal"; // We'll create this component

const SheetHeader = ({
  sheet,
  setRunId,
  hasChanges,
  onSave,
  sheetRunning,
  runId,
}) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [open, setOpen] = useState(false);
  const [isPreviousRunsModalOpen, setIsPreviousRunsModalOpen] = useState(false);

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
            <ClickAwayListener onClickAway={() => setOpen(false)}>
              <div>
                <Tooltip title={"Settings"}>
                  <Button
                    variant="contained"
                    size="medium"
                    onClick={(event) => {
                      setAnchorEl(event.currentTarget);
                      setOpen((prev) => !prev);
                    }}
                    sx={{
                      bgcolor: "gray.main",
                      "&:hover": { bgcolor: "white" },
                      color: "#999",
                      minWidth: "40px",
                      padding: "5px",
                      borderRadius: "4px !important",
                    }}
                  >
                    <SettingsIcon />
                  </Button>
                </Tooltip>
                <Popper open={open} anchorEl={anchorEl} placement="bottom-end">
                  <Paper>
                    <MenuList>
                      <MenuItem
                        onClick={() => {
                          setIsPreviousRunsModalOpen(true);
                          setOpen(false);
                        }}
                      >
                        <ListItemIcon>
                          <HistoryIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText>Previous Runs</ListItemText>
                      </MenuItem>
                      <MenuItem
                        onClick={() => {
                          setOpen(false);
                        }}
                      >
                        <ListItemIcon>
                          <AutorenewIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText>Automated Runs</ListItemText>
                      </MenuItem>
                      <Divider />
                      <MenuItem
                        onClick={() => {
                          setOpen(false);
                        }}
                      >
                        <ListItemIcon>
                          <DeleteIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText>Delete Sheet</ListItemText>
                      </MenuItem>
                    </MenuList>
                  </Paper>
                </Popper>
              </div>
            </ClickAwayListener>
          </Stack>
        </Stack>
      </Typography>
      <PreviousRunsModal
        open={isPreviousRunsModalOpen}
        onClose={() => setIsPreviousRunsModalOpen(false)}
        sheetUuid={sheet.uuid}
      />
    </Stack>
  );
};

export default SheetHeader;
