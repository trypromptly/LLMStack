import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";

export function LoggedOutModal({
  visibility,
  handleCancelCb,
  data,
  title,
  message,
}) {
  // fuction to store state in local storage before redirecting to login page
  const handleLogin = () => {
    if (data) localStorage.setItem("shareCode", data);
    window.location.href = "/login";
  };

  return (
    <Dialog
      title={title ? title : "Logged Out"}
      open={visibility}
      onCancel={handleCancelCb}
      footer={null}
    >
      <DialogTitle id="logged-out-modal-title">Logged Out</DialogTitle>
      <DialogContent>
        <DialogContentText>
          <Box>
            {message ? (
              message
            ) : (
              <p>
                You are logged out. Please{" "}
                <Button
                  type="link"
                  onClick={handleLogin}
                  style={{ padding: "0px" }}
                >
                  login
                </Button>{" "}
                or{" "}
                <Button
                  type="link"
                  onClick={handleLogin}
                  style={{ padding: "0px" }}
                >
                  signup
                </Button>{" "}
                to proceed.
              </p>
            )}
          </Box>
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
