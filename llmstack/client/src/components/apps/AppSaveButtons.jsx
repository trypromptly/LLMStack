import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
  TextField,
} from "@mui/material";
import { useState } from "react";

function AppSaveDialog({ open, setOpen, saveApp, postSave = null }) {
  const [comment, setComment] = useState("Update app");
  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>Create New Version</DialogTitle>
      <DialogContent>
        <DialogContentText>
          To save a new version of the app, please provide a description for the
          change.
        </DialogContentText>
        <TextField
          autoFocus
          margin="dense"
          id="name"
          label="Describe changes"
          type="text"
          fullWidth
          variant="standard"
          value={comment}
          required={true}
          onChange={(e) => setComment(e.target.value)}
          multiline
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} sx={{ textTransform: "none" }}>
          Cancel
        </Button>
        <Button
          onClick={() => {
            saveApp(false, comment).finally(() => {
              setComment("Update app");
              setOpen(false);

              if (postSave) {
                postSave();
              }
            });
          }}
          variant="contained"
          sx={{ textTransform: "none" }}
        >
          Save Version
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function AppSaveButtons({ saveApp, postSave = null }) {
  const [open, setOpen] = useState(false);
  return (
    <Stack direction="row" gap={1} sx={{ marginBottom: "50px" }}>
      <AppSaveDialog
        open={open}
        setOpen={setOpen}
        saveApp={saveApp}
        postSave={postSave}
      />
      <Button
        onClick={() => {
          saveApp().finally(() => {
            if (postSave) {
              postSave();
            }
          });
        }}
        variant="contained"
        style={{
          textTransform: "none",
          margin: "20px 0",
          backgroundColor: "#ccc",
          color: "#000",
        }}
      >
        Save Draft
      </Button>
      <Button
        onClick={() => setOpen(true)}
        variant="contained"
        style={{ textTransform: "none", margin: "20px 0" }}
      >
        Save App
      </Button>
    </Stack>
  );
}
