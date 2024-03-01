import {
  Button,
  Dialog,
  DialogContent,
  Divider,
  Link,
  Stack,
  Typography,
} from "@mui/material";
import { styled } from "@mui/system";
import logo from "../assets/icon-transparent.png";
import googleIcon from "../assets/images/icons/google.svg";

const Logo = styled("img")({
  width: "50px",
  margin: "0 auto",
});

function LoginDialog({ open, handleClose, redirectPath, loginMessage }) {
  return (
    <Dialog
      open={open}
      onClose={handleClose}
      aria-labelledby="login-dialog-title"
      aria-describedby="login-dialog-description"
      maxWidth="xs"
      sx={{
        textAlign: "center",
      }}
    >
      <Stack m={8}>
        <Logo src={logo} alt="logo" />
        <Typography
          sx={{
            fontSize: "48px",
            fontWeight: 600,
            color: "#0a398d",
          }}
        >
          Promptly
        </Typography>
      </Stack>
      <Divider />
      <DialogContent sx={{ backgroundColor: "#f7f7f7" }}>
        <Stack sx={{ alignItems: "center", margin: "1em" }} gap={8}>
          <Typography sx={{ fontSize: "18px", maxWidth: "250px" }}>
            {loginMessage || "Please sign in to continue using the platform."}
          </Typography>
          <Link
            underline="none"
            href={
              redirectPath
                ? `/accounts/google/login/?next=${redirectPath}`
                : "/accounts/google/login/"
            }
          >
            <Button
              variant="outlined"
              size="large"
              sx={{
                textTransform: "none",
                fontSize: "18px",
                width: "300px",
                padding: "10px",
                backgroundColor: "#fff",
              }}
            >
              <img src={googleIcon} alt="Google" width={"24px"} />
              &nbsp; Continue with Google
            </Button>
          </Link>
          <Typography
            sx={{
              fontSize: "16px",
              color: "#2f3437",
              lineHeight: "1.8em",
              border: "1px solid #e0e0e0",
              padding: "10px",
              borderRadius: "5px",
              backgroundColor: "#fff",
            }}
          >
            Access thousands of Generative AI applications for free. Use
            ChatGPT, GPT-4, Claude 2, DALLE 3, and others - all on Promptly.
          </Typography>
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
      </DialogContent>
    </Dialog>
  );
}

export default LoginDialog;
