import React, { useState, useCallback } from "react";
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
import PreviousRunsModal from "./PreviousRunsModal";
import SheetDeleteDialog from "./SheetDeleteDialog";
import { useSetRecoilState } from "recoil";
import { sheetsListSelector } from "../../data/atoms";
import SaveIcon from "@mui/icons-material/Save";
import DownloadIcon from "@mui/icons-material/Download";

const SheetHeader = ({
  sheet,
  runId,
  setRunId,
  hasChanges,
  onSave,
  sheetRunning,
  setSheetRunning,
}) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [open, setOpen] = useState(false);
  const [isPreviousRunsModalOpen, setIsPreviousRunsModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const setSheets = useSetRecoilState(sheetsListSelector);

  const runSheet = useCallback(() => {
    const runSheetAction = () => {
      axios()
        .post(`/api/sheets/${sheet.uuid}/run`)
        .then((response) => {
          setRunId(response.data.run_id);
          setSheetRunning(true);
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
  }, [sheet.uuid, hasChanges, onSave, setRunId, setSheetRunning]);

  const cancelSheetRun = useCallback(() => {
    if (!runId) {
      return;
    }

    axios()
      .post(`/api/sheets/${sheet.uuid}/runs/${runId}/cancel`)
      .then(() => {
        setRunId(null);
        setSheetRunning(false);
      })
      .catch((error) => {
        console.error(error);
      });
  }, [sheet.uuid, runId, setRunId, setSheetRunning]);

  const handleDeleteSheet = () => {
    axios()
      .delete(`/api/sheets/${sheet.uuid}`)
      .then(() => {
        axios()
          .get("/api/sheets")
          .then((response) => {
            setSheets(response.data);
          })
          .catch((error) => {
            console.error("Error fetching updated sheets list:", error);
          });
        enqueueSnackbar("Sheet deleted successfully", { variant: "success" });
        navigate("/sheets");
      })
      .catch((error) => {
        console.error("Error deleting sheet:", error);
        enqueueSnackbar("Failed to delete sheet", { variant: "error" });
      });
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
            <div>
              <Tooltip title="Save changes">
                <Button
                  onClick={onSave}
                  disabled={!hasChanges}
                  variant="contained"
                  sx={{
                    bgcolor: "gray.main",
                    "&:hover": { bgcolor: "white" },
                    color: "#999",
                    minWidth: "40px",
                    padding: "5px",
                    borderRadius: "4px !important",

                    "&:disabled": {
                      bgcolor: "#ccc",
                      color: "#999",
                      padding: "5px",
                      borderRadius: "4px !important",
                    },
                  }}
                >
                  <SaveIcon />
                </Button>
              </Tooltip>
            </div>
            {!sheetRunning && (
              <div>
                <Tooltip title="Download CSV">
                  <Button
                    onClick={() =>
                      window.open(
                        `/api/sheets/${sheet.uuid}/download`,
                        "_blank",
                      )
                    }
                    variant="contained"
                    size="medium"
                    sx={{
                      bgcolor: "gray.main",
                      "&:hover": { bgcolor: "white" },
                      color: "#999",
                      minWidth: "40px",
                      padding: "5px",
                      borderRadius: "4px !important",
                    }}
                  >
                    <DownloadIcon />
                  </Button>
                </Tooltip>
              </div>
            )}
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
                          setIsDeleteDialogOpen(true);
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
            <Tooltip
              title={
                sheetRunning ? "Sheet is already running" : "Run the sheet"
              }
            >
              <span>
                <Button
                  variant="contained"
                  size="medium"
                  onClick={sheetRunning ? cancelSheetRun : runSheet}
                  sx={{
                    bgcolor: sheetRunning ? "warning.main" : "success.main",
                    "&:hover": {
                      bgcolor: sheetRunning ? "warning.dark" : "success.dark",
                    },
                    minWidth: "40px",
                    padding: "5px",
                    borderRadius: "4px !important",
                  }}
                >
                  {sheetRunning ? <PauseIcon /> : <PlayArrowIcon />}
                </Button>
              </span>
            </Tooltip>
          </Stack>
        </Stack>
      </Typography>
      <PreviousRunsModal
        open={isPreviousRunsModalOpen}
        onClose={() => setIsPreviousRunsModalOpen(false)}
        sheetUuid={sheet.uuid}
      />
      <SheetDeleteDialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDeleteSheet}
        sheetName={sheet.name}
      />
    </Stack>
  );
};

export default SheetHeader;
