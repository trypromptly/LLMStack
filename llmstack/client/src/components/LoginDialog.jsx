import {
  Typography,
  Button,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Link,
  Stack,
} from "@mui/material";

function LoginDialog({ open, handleClose, redirectPath }) {
  return (
    <Dialog
      open={open}
      onClose={handleClose}
      aria-labelledby="login-dialog-title"
      aria-describedby="login-dialog-description"
    >
      <DialogTitle
        id="login-dialog-title"
        sx={{ display: "flex", justifyContent: "center" }}
      >
        <Typography variant="h4">Sign in to continue</Typography>
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="login-dialog-description">
          <Stack sx={{ alignItems: "center" }}>
            <Typography variant="body" gutterBottom>
              Access 100+ community applications for free. Use ChatGPT, GPT-4,
              Claude 2, DALLE 3, and others - all on Promptly.
            </Typography>
            <Stack sx={{ width: "100%", alignItems: "center" }}>
              <Link
                underline="none"
                href={
                  redirectPath ? `/login?redirectUrl=${redirectPath}` : "/login"
                }
              >
                <Button variant="contained" autoFocus>
                  Login
                </Button>
              </Link>
            </Stack>
            <Typography variant="caption" sx={{ marginTop: "4px" }}>
              By continuing, you agree to our{" "}
              <span>
                <a href="https://www.trypromptly.com/tos">Terms of Service</a>
              </span>{" "}
              and{" "}
              <span>
                <a href="https://www.trypromptly.com/privacy">Privacy Policy</a>
              </span>
            </Typography>
          </Stack>
        </DialogContentText>
      </DialogContent>
    </Dialog>
  );
}

export default LoginDialog;
