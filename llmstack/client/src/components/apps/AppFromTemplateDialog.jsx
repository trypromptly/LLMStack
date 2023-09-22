import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

export function AppFromTemplateDialog({
  open,
  setOpen,
  appName,
  setAppName,
  createApp,
  appTemplate,
}) {
  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogContent>
        <Typography
          style={{ paddingTop: 5, fontSize: "20px", fontWeight: 500 }}
        >
          {appTemplate?.name}
        </Typography>
        <Typography style={{ paddingTop: 10, fontSize: "14px", color: "#555" }}>
          {appTemplate?.description}
          {appTemplate?.example_app_uuid && " Try it out "}
          {appTemplate?.example_app_uuid && (
            <a
              href={`https://trypromptly.com/app/${appTemplate?.example_app_uuid}`}
              target="_blank"
              rel="noreferrer"
            >
              here
            </a>
          )}
        </Typography>
        <Stack gap={0.5} direction="row" mt={2}>
          {appTemplate?.categories?.map((tag, index) => (
            <Chip
              key={index}
              label={tag?.name}
              variant="outlined"
              size="small"
              sx={{ borderRadius: "5px" }}
            />
          ))}
        </Stack>
        <Typography
          style={{
            paddingTop: 20,
            paddingBottom: 5,
            fontSize: "16px",
          }}
        >
          To begin creating your application, please provide a name.
        </Typography>
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
