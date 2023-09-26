import { useState } from "react";
import { useLocation } from "react-router-dom";

import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import { styled } from "@mui/system";
import { postData } from "./dataUtil";

import logo from "../assets/llmstack-logo.svg";

const Logo = styled("img")({
  width: "60%",
  marginBottom: 20,
});

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const redirectUrl = searchParams.get("redirectUrl");
  const onSignInClick = async (e) => {
    e.preventDefault();

    if (!username || !password) {
      return;
    }

    await postData(
      "/api/login",
      {
        username: username,
        password: password,
      },
      () => {},
      (result) => {
        if (redirectUrl) {
          window.location.href = redirectUrl;
        } else {
          window.location.href = "/";
        }
        
      },
    );
  };

  return (
    <Container maxWidth="xs">
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          minHeight: "100vh",
          justifyContent: "center",
        }}
      >
        <Paper elevation={3} sx={{ p: 2, width: "100%", textAlign: "center" }}>
          <Logo
            src={logo}
            alt="logo"
            sx={{
              mt: 6,
            }}
          />
          <Box component="form" noValidate sx={{ margin: 3 }}>
            <TextField
              variant="outlined"
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              onChange={(e) => setUsername(e.target.value)}
              value={username}
            />
            <TextField
              variant="outlined"
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
              value={password}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              sx={{ mt: 4, mb: 4, textTransform: "none" }}
              onClick={onSignInClick}
            >
              Sign In
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
