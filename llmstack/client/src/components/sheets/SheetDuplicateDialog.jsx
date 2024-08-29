import React, { useState, useEffect } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Checkbox,
  FormControlLabel,
  Stack,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";
import { useNavigate } from "react-router-dom";

export function SheetDuplicateDialog({ open, setOpen, sheet, onDuplicate }) {
  const [newSheetName, setNewSheetName] = useState("");
  const [newSheetDescription, setNewSheetDescription] = useState("");
  const [excludeCellData, setExcludeCellData] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (sheet) {
      setNewSheetName(`${sheet.name || ""} (Copy)`);
      setNewSheetDescription(sheet.description || "");
    }
  }, [sheet]);

  const handleClose = () => {
    setOpen(false);
  };

  const handleDuplicate = () => {
    if (!sheet) return;

    let payload = {
      name: newSheetName,
      description: newSheetDescription,
      columns: sheet.columns || {},
      formula_cells: sheet.formula_cells || {},
      total_rows: sheet.total_rows || 1,
      total_columns: sheet.total_columns || 26,
    };

    const sendRequest = (payloadWithCells) => {
      axios()
        .post("/api/sheets", payloadWithCells)
        .then((response) => {
          onDuplicate(response.data);
          setOpen(false);
          navigate(`/sheets/${response.data.uuid}`);
        })
        .catch((error) => {
          enqueueSnackbar(`Error duplicating sheet: ${error.message}`, {
            variant: "error",
          });
        });
    };

    if (!excludeCellData) {
      // Fetch cell data from the server if it's not already available
      if (Object.keys(sheet?.cells || {}).length === 0) {
        axios()
          .get(`/api/sheets/${sheet.uuid}?include_cells=true`)
          .then((response) => {
            payload.cells = response.data.cells;
            sendRequest(payload);
          });
      } else {
        payload.cells = sheet.cells;
        sendRequest(payload);
      }
    } else {
      sendRequest(payload);
    }
  };

  if (!sheet) return null;

  return (
    <Dialog open={open} onClose={handleClose} fullWidth>
      <DialogTitle>Duplicate Sheet</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 2 }}>
          <TextField
            label="New Sheet Name"
            value={newSheetName}
            onChange={(e) => setNewSheetName(e.target.value)}
            fullWidth
          />
          <TextField
            label="Description"
            value={newSheetDescription}
            onChange={(e) => setNewSheetDescription(e.target.value)}
            multiline
            rows={2}
            fullWidth
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={excludeCellData}
                onChange={(e) => setExcludeCellData(e.target.checked)}
              />
            }
            label="Create without cell data"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleDuplicate} variant="contained">
          Duplicate
        </Button>
      </DialogActions>
    </Dialog>
  );
}
