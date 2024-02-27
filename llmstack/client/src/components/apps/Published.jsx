import { useEffect, useRef, useState } from "react";
import {
  AppBar,
  Box,
  Button,
  Container,
  Fab,
  Stack,
  SvgIcon,
  Toolbar,
  Typography,
} from "@mui/material";
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  QuestionAnswer as QuestionAnswerIcon,
} from "@mui/icons-material";
import { ReactComponent as GithubIcon } from "../../assets/images/icons/github.svg";
import { TwitterIcon, TwitterShareButton } from "react-share";
import { AppRenderer } from "./renderer/AppRenderer";
import logo from "../../assets/logo.png";

const SITE_NAME = process.env.REACT_APP_SITE_NAME || "LLMStack";

export const PublishedAppHeader = ({ appName, appLogo, appIsShareable }) => {
  return (
    <AppBar
      position="static"
      sx={{
        backgroundColor: "#fff",
        color: "#000",
      }}
    >
      <Container maxWidth="xl">
        <Toolbar
          disableGutters
          sx={{
            width: "100%",
            margin: "0 auto",
          }}
        >
          <a
            href={appLogo ? "/" : "https://trypromptly.com"}
            target="_blank"
            rel="noreferrer"
          >
            <img src={appLogo || logo} alt="Promptly" style={{ height: 30 }} />
          </a>
          <Box sx={{ flexGrow: 1 }} />
          {SITE_NAME === "LLMStack" && (
            <SvgIcon
              component={GithubIcon}
              sx={{ width: "54px", height: "54px" }}
              viewBox="-10 -4 28 26"
              onClick={() => {
                window.location.href =
                  "https://github.com/trypromptly/llmstack";
              }}
            />
          )}
          {appIsShareable && (
            <TwitterShareButton
              url={window.location.href}
              title={`Check out ${appName} on Promptly!\n\n`}
              via={"TryPromptly"}
              hashtags={["NoCodeAI"]}
            >
              <TwitterIcon size={30} round={true} />
            </TwitterShareButton>
          )}
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export const PublishedAppError = ({ error, isLoggedIn }) => (
  <Box
    style={{
      justifyContent: "center",
      paddingTop: 50,
      display: "flex",
      flexDirection: "column",
      textAlign: "center",
      maxWidth: 600,
      margin: "0 auto",
      gap: 10,
    }}
  >
    <Typography variant="body2">{error}</Typography>
    <Button
      variant="contained"
      sx={{ textTransform: "none", margin: "auto" }}
      onClick={() => {
        window.location.href = isLoggedIn
          ? "/hub"
          : `/login?redirectUrl=${window.location.pathname}`;
      }}
    >
      {isLoggedIn ? "Go To Hub" : "Login"}
    </Button>
  </Box>
);

export const PublishedAppFooter = () => {
  return (
    <Box
      sx={{
        justifyContent: "center",
        textAlign: "center",
        bottom: "0px",
        margin: "0 auto",
        paddingTop: "10px",
      }}
    >
      <Typography sx={{ textAlign: "center" }} variant="caption">
        Powered by{" "}
        <a href="https://trypromptly.com" target="_blank" rel="noreferrer">
          Promptly
        </a>
      </Typography>
    </Box>
  );
};

export const PublishedApp = ({ ws, app, error, isLoggedIn, isMobile }) => {
  return (
    <Stack container spacing={2}>
      <PublishedAppHeader
        appName={app.name}
        appLogo={app.logo}
        appIsShareable={app.is_shareable}
      />
      <Box>
        <p></p>
      </Box>
      {error && <PublishedAppError error={error} isLoggedIn={isLoggedIn} />}
      <Box>
        <AppRenderer app={app} isMobile={isMobile} ws={ws} />
      </Box>
      {(app.has_footer ||
        !process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT) && (
        <PublishedAppFooter />
      )}
    </Stack>
  );
};

export const PublishedAppWebEmbed = ({
  ws,
  app,
  error,
  isLoggedIn,
  isMobile,
}) => {
  return (
    <Stack container spacing={2}>
      {error && <PublishedAppError error={error} isLoggedIn={isLoggedIn} />}
      <Box>
        <AppRenderer app={app} isMobile={isMobile} ws={ws} />
      </Box>
      {(app.has_footer ||
        !process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT) && (
        <PublishedAppFooter />
      )}
    </Stack>
  );
};

export const PublishedAppChatEmbed = ({
  ws,
  app,
  error,
  isLoggedIn,
  isMobile,
}) => {
  const chatBubbleRef = useRef(null);
  const [showChat, setShowChat] = useState(false);
  const [chatBubbleStyle, setChatBubbleStyle] = useState({
    backgroundColor: app?.data?.config?.window_color || "#0f477e",
    color: "white",
    position: "fixed",
    right: 16,
    bottom: 16,
  });

  useEffect(() => {
    setChatBubbleStyle({
      ...chatBubbleStyle,
      backgroundColor: app?.data?.config?.window_color || "#0f477e",
    });
  }, [app?.data?.config?.window_color, chatBubbleStyle]);

  return (
    <Stack container spacing={2}>
      <Fab
        style={chatBubbleStyle}
        onClick={() => setShowChat(!showChat)}
        variant={app?.data?.config?.chat_bubble_text ? "extended" : "circular"}
        ref={chatBubbleRef}
      >
        {showChat ? (
          <KeyboardArrowDownIcon />
        ) : app?.data?.config?.chat_bubble_text ? (
          <span>{app?.data?.config?.chat_bubble_text}</span>
        ) : (
          <QuestionAnswerIcon />
        )}
      </Fab>
      {error && <PublishedAppError error={error} isLoggedIn={isLoggedIn} />}
      <Box>
        <AppRenderer app={app} isMobile={isMobile} ws={ws} />
      </Box>
      {(app.has_footer ||
        !process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT) && (
        <PublishedAppFooter />
      )}
    </Stack>
  );
};
