import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  Typography,
} from "@mui/material";

export function AppNameDialog({
  open,
  setOpen,
  appName,
  setAppName,
  createApp,
  preText = null,
}) {
  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>Create a New App</DialogTitle>
      <DialogContent>
        <DialogContentText>
          {preText}
          <Typography style={{ paddingTop: 5, fontSize: "18px" }}>
            To begin creating your application, please provide a name.
          </Typography>
        </DialogContentText>
        <TextField
          autoFocus
          margin="dense"
          id="name"
          label="App name"
          type="text"
          fullWidth
          variant="standard"
          value={appName}
          required={true}
          onChange={(e) => setAppName(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} sx={{ textTransform: "none" }}>
          Cancel
        </Button>
        <Button
          onClick={createApp}
          variant="contained"
          sx={{ textTransform: "none" }}
        >
          Create App
        </Button>
      </DialogActions>
    </Dialog>
  );
}
