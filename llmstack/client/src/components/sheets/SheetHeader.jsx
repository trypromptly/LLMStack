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
  CircularProgress,
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
  selectedRows,
  deleteSelectedRows,
}) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [open, setOpen] = useState(false);
  const [isPreviousRunsModalOpen, setIsPreviousRunsModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const setSheets = useSetRecoilState(sheetsListSelector);
  const [isSaving, setIsSaving] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  const runSheet = useCallback(() => {
    const runSheetAction = () => {
      setIsRunning(true);
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
        })
        .finally(() => {
          setIsRunning(false);
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

  const handleSave = () => {
    setIsSaving(true);
    onSave().finally(() => {
      setIsSaving(false);
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
              <span>
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
              </span>
            </Tooltip>
            <Stack>
              {sheet?.name}
              <Typography variant="caption" sx={{ color: "#666" }}>
                {sheet?.description || sheet?.data?.description || ""}
              </Typography>
            </Stack>
          </Stack>
          <Stack direction={"row"} gap={1} sx={{ marginRight: "-8px" }}>
            {selectedRows.length > 0 && (
              <Tooltip
                title={`Delete ${selectedRows.length} selected row${
                  selectedRows.length > 1 ? "s" : ""
                }`}
              >
                <span>
                  <Button
                    onClick={deleteSelectedRows}
                    variant="contained"
                    sx={{
                      bgcolor: "gray.main",
                      "&:hover": {
                        bgcolor: "gray.dark",
                        "& > svg": { color: "white" },
                      },
                      minWidth: "40px",
                      padding: "5px",
                      borderRadius: "4px !important",
                    }}
                  >
                    <DeleteIcon
                      color="error"
                      sx={{ "&:hover": { color: "white" } }}
                    />
                  </Button>
                </span>
              </Tooltip>
            )}
            {hasChanges && (
              <Tooltip title="Save changes">
                <span>
                  <Button
                    onClick={handleSave}
                    variant="contained"
                    disabled={isSaving}
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
                    {isSaving ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      <SaveIcon />
                    )}
                  </Button>
                </span>
              </Tooltip>
            )}
            {!sheetRunning && (
              <div>
                <Tooltip title="Download CSV">
                  <span>
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
                  </span>
                </Tooltip>
              </div>
            )}
            <ClickAwayListener onClickAway={() => setOpen(false)}>
              <div>
                <Tooltip title={"Settings"}>
                  <span>
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
                  </span>
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
                  disabled={isRunning}
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
                  {isRunning ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : sheetRunning ? (
                    <PauseIcon />
                  ) : (
                    <PlayArrowIcon />
                  )}
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
