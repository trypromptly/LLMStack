import React, { useState, useCallback, useEffect } from "react";
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
import UploadIcon from "@mui/icons-material/Upload";
import { useNavigate } from "react-router-dom";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";
import PreviousRunsModal from "./PreviousRunsModal";
import ScheduleRunsModal from "./ScheduleRunsModal";
import SheetDeleteDialog from "./SheetDeleteDialog";
import SchemaModal from "./SchemaModal";
import { useSetRecoilState } from "recoil";
import { sheetsListSelector } from "../../data/atoms";
import SaveIcon from "@mui/icons-material/Save";
import DownloadIcon from "@mui/icons-material/Download";
import yaml from "js-yaml";

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
  selectedGrid = [],
}) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [open, setOpen] = useState(false);
  const [isPreviousRunsModalOpen, setIsPreviousRunsModalOpen] = useState(false);
  const [isScheduleRunsModalOpen, setIsScheduleRunsModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const setSheets = useSetRecoilState(sheetsListSelector);
  const [isSaving, setIsSaving] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isCommandPressed, setIsCommandPressed] = useState(false);
  const [isExportSchemaModalOpen, setIsExportSchemaModalOpen] = useState(false);

  const getYamlSchemaFromSheet = useCallback(() => {
    let schema = {};

    schema["name"] = sheet.name;
    schema["description"] = sheet.description;
    schema["total_rows"] = sheet.total_rows;
    schema["total_columns"] = sheet.total_columns;
    schema["columns"] = sheet.columns;

    // Include cells that only have a formula
    const cellsWithFormula = Object.values(sheet?.cells).filter(
      (cell) => cell.formula,
    );
    schema["cells"] = {};
    cellsWithFormula.forEach((cell) => {
      let filteredCell = { ...cell };
      delete filteredCell.value;
      delete filteredCell.status;
      delete filteredCell.error;

      schema["cells"][`${cell.col_letter}${cell.row}`] = filteredCell;
    });

    return yaml.dump(schema);
  }, [
    sheet?.cells,
    sheet?.name,
    sheet?.description,
    sheet?.total_rows,
    sheet?.total_columns,
    sheet?.columns,
  ]);

  // Add event listeners for keydown and keyup
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.metaKey || e.ctrlKey) {
        setIsCommandPressed(true);
      }
    };

    const handleKeyUp = (e) => {
      if (!e.metaKey && !e.ctrlKey) {
        setIsCommandPressed(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  const runSheet = useCallback(() => {
    const runSheetAction = () => {
      setIsRunning(true);
      axios()
        .post(`/api/sheets/${sheet.uuid}/run`, {
          selected_grid: isCommandPressed ? selectedGrid : null,
        })
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
  }, [
    sheet.uuid,
    hasChanges,
    onSave,
    setRunId,
    setSheetRunning,
    selectedGrid,
    isCommandPressed,
  ]);

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
                          setIsScheduleRunsModalOpen(true);
                          setOpen(false);
                        }}
                      >
                        <ListItemIcon>
                          <AutorenewIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText>Automated Runs</ListItemText>
                      </MenuItem>
                      <MenuItem
                        onClick={() => {
                          setIsExportSchemaModalOpen(true);
                          setOpen(false);
                        }}
                      >
                        <ListItemIcon>
                          <UploadIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText>Export Schema</ListItemText>
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
                sheetRunning
                  ? "Sheet is already running"
                  : isCommandPressed
                    ? "Run selected cells"
                    : "Run the sheet"
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
      {isScheduleRunsModalOpen && (
        <ScheduleRunsModal
          open={isScheduleRunsModalOpen}
          onClose={() => setIsScheduleRunsModalOpen(false)}
          sheetUuid={sheet.uuid}
        />
      )}
      <SheetDeleteDialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDeleteSheet}
        sheetName={sheet.name}
      />
      <SchemaModal
        open={isExportSchemaModalOpen}
        onClose={() => setIsExportSchemaModalOpen(false)}
        sheetUuid={sheet.uuid}
        schema={getYamlSchemaFromSheet()}
      />
    </Stack>
  );
};

export default SheetHeader;
