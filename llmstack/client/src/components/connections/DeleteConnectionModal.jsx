import { useState } from "react";
import {
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
} from "@mui/material";

function DeleteConnectionModal({ open, onCancelCb, onDeleteCb, connection }) {
  const [deleteValue, setDeleteValue] = useState("");

  if (!open || !connection) {
    return null;
  }

  return (
    <Dialog open={open} onClose={onCancelCb} fullWidth>
      <DialogTitle>Delete Connection</DialogTitle>
      <DialogContent>
        <DialogContentText>
          <Alert severity="warning">
            {`Are you sure you want to delete ${connection.name}? This action cannot
            be undone.`}
          </Alert>
        </DialogContentText>

        <TextField
          autoFocus
          margin="dense"
          id="name"
          label="DELETE"
          placeholder="Type DELETE to confirm"
          type="text"
          fullWidth
          variant="standard"
          value={deleteValue}
          required={true}
          onChange={(e) => setDeleteValue(e.target.value)}
        />
      </DialogContent>

      <DialogActions>
        <Button
          onClick={onCancelCb}
          variant="outlined"
          style={{ textTransform: "none" }}
        >
          Cancel
        </Button>
        <Button
          onClick={() => onDeleteCb(connection).finally(() => onCancelCb())}
          variant="contained"
          style={{ textTransform: "none" }}
          disabled={deleteValue !== "DELETE"}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default DeleteConnectionModal;
