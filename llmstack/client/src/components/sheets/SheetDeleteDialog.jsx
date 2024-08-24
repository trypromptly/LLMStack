import React from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
} from "@mui/material";

function SheetDeleteDialog({ open, onClose, onConfirm, sheetName }) {
  const [deleteConfirmation, setDeleteConfirmation] = React.useState("");
  const [error, setError] = React.useState("");

  const handleConfirm = () => {
    if (deleteConfirmation === "DELETE") {
      onConfirm();
      setDeleteConfirmation("");
      setError("");
    } else {
      setError("Please type DELETE to confirm");
    }
  };

  return (
    <Dialog open={open} onClose={onClose} onClick={(e) => e.stopPropagation()}>
      <DialogTitle>Confirm Delete</DialogTitle>
      <DialogContent>
        <DialogContentText>
          <Alert severity="warning">
            Are you sure you want to delete the sheet "{sheetName}"? This action
            cannot be undone.
          </Alert>
        </DialogContentText>
        <TextField
          fullWidth
          margin="normal"
          variant="outlined"
          value={deleteConfirmation}
          onChange={(e) => setDeleteConfirmation(e.target.value)}
          placeholder="Type DELETE to confirm"
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={deleteConfirmation !== "DELETE"}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default SheetDeleteDialog;
