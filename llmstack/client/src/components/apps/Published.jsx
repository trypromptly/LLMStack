import { lazy, useEffect, useRef, useState } from "react";
import {
  AppBar,
  Avatar,
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
import logo from "../../assets/logo.png";
import "./Published.css";

const AppRenderer = lazy(() => import("./renderer/AppRenderer"));

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
        marginTop: "0 !important",
        padding: "5px",
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
    <Stack
      container
      spacing={2}
      height={isMobile ? "calc(100vh - 50px)" : "100vh"}
    >
      <PublishedAppHeader
        appName={app.name}
        appLogo={app.logo}
        appIsShareable={app.is_shareable}
      />
      <Box>
        <p></p>
      </Box>
      {error && <PublishedAppError error={error} isLoggedIn={isLoggedIn} />}
      <Box sx={{ height: "100%" }}>
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
    <Stack container spacing={2} sx={{ height: "calc(100vh - 170px)" }}>
      {error && <PublishedAppError error={error} isLoggedIn={isLoggedIn} />}
      <Box sx={{ height: "100%" }}>
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
    document.body.style = "background: transparent";
    document.getElementsByClassName("root").style = "background: transparent";

    try {
      const style = JSON.parse(app?.data?.config?.chat_bubble_style || "{}");
      setChatBubbleStyle((prevBubbleStyle) => ({
        ...prevBubbleStyle,
        backgroundColor: app?.data?.config?.window_color || "#0f477e",
        ...style,
      }));
    } catch (e) {
      console.error(e);
    }

    if (showChat) {
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      const isMobile =
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
          userAgent,
        );
      const width = isMobile ? "100%" : "400px";
      const height = isMobile ? "90vh" : "700px";
      window.parent.postMessage(
        { width, height, type: "promptly-embed-open" },
        "*",
      );
    } else {
      setTimeout(() => {
        window.parent.postMessage(
          {
            type: "promptly-embed-resize",
            width: chatBubbleRef?.current?.clientWidth || "auto",
            height: chatBubbleRef?.current?.clientHeight || "auto",
          },
          "*",
        );
      }, 200);
    }
  }, [
    showChat,
    app?.data?.config?.chat_bubble_style,
    app?.data?.config?.window_color,
  ]);

  return (
    <>
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
      {showChat && (
        <div
          className={`chat-container embedded ${
            showChat ? "maximized" : "minimized"
          }`}
          style={{
            width: isMobile ? "90%" : "100%",
          }}
        >
          <div
            style={{
              display: "flex",
              backgroundColor: app?.data?.config.window_color || "#0f477e",
              borderRadius: "8px 8px 0px 0px",
            }}
          >
            {(app.icon || app?.data?.config?.assistant_image) && (
              <Avatar
                src={app.icon || app.data?.config?.assistant_image}
                alt="Bot"
                style={{ margin: "10px 8px", border: "solid 1px #ccc" }}
              />
            )}
            <span
              style={{
                margin: "auto 0px",
                fontWeight: 600,
                fontSize: "18px",
                color: "white",
                padding:
                  app.icon || app?.data?.config?.assistant_image
                    ? "inherit"
                    : "16px",
              }}
            >
              {app?.name}
            </span>
          </div>
          <Box sx={{ margin: 2 }}>
            <PublishedAppWebEmbed
              ws={ws}
              app={app}
              error={error}
              isLoggedIn={isLoggedIn}
              isMobile={isMobile}
            />
          </Box>
        </div>
      )}
    </>
  );
};
