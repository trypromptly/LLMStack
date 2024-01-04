import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { axios } from "../data/axios";
import { Ws } from "../data/ws";
import ReactGA from "react-ga4";
import {
  AppBar,
  Box,
  Button,
  Container,
  Stack,
  SvgIcon,
  Toolbar,
  Typography,
} from "@mui/material";
import { TwitterIcon, TwitterShareButton } from "react-share";
import { useRecoilValue } from "recoil";
import { isMobileState, isLoggedInState } from "../data/atoms";
import { AgentRenderer } from "../components/apps/AgentRenderer";
import { WebChatRender } from "../components/apps/WebChatRender";
import { WebAppRenderer } from "../components/apps/WebAppRenderer";
import { ReactComponent as GithubIcon } from "../assets/images/icons/github.svg";
import logo from "../assets/logo.png";

const SITE_NAME = process.env.REACT_APP_SITE_NAME || "LLMStack";

function AppRenderPage({ headless = false }) {
  const { publishedAppId, embed, chatBubble } = useParams();
  const [app, setApp] = useState({});
  const [wsUrl, setWsUrl] = useState(null);
  const [ws, setWs] = useState(null);
  const [error, setError] = useState(null);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    ReactGA.initialize(
      process.env.REACT_APP_GA_MEASUREMENT_ID || "G-WV60HC9CHD",
      {
        gaOptions: {
          cookieFlags: "SameSite=None;Secure",
        },
      },
    );
  }, []);

  const isMobile = useRecoilValue(isMobileState);
  const isLoggedIn = useRecoilValue(isLoggedInState);

  useEffect(() => {
    if (publishedAppId) {
      axios()
        .get(`/api/app/${publishedAppId}`)
        .then(
          (response) => {
            setApp(response.data);
            setWsUrl(`${wsUrlPrefix}/apps/${response?.data?.uuid}`);
            document.title = `${response.data.name} | ${
              process.env.REACT_APP_SITE_NAME || "LLMStack"
            }`;
            ReactGA.send({
              hitType: "pageview",
              page: window.location.href,
              title: document.title,
            });
          },
          (error) => {
            console.log(error);
            setError(error?.response?.data?.message);
          },
        )
        .catch((error) => {
          setError(error?.response?.data?.message);
        });
    }
  }, [publishedAppId, setApp, wsUrlPrefix]);

  useEffect(() => {
    if (wsUrl && !wsUrl.endsWith("/ws") && !ws) {
      setWs(new Ws(wsUrl));
    }
  }, [ws, wsUrl]);

  return app?.type?.slug === "text-chat" && embed && chatBubble ? (
    <WebChatRender app={app} isMobile={isMobile} embed={embed} ws={ws} />
  ) : app?.type?.slug === "agent" && embed && chatBubble ? (
    <AgentRenderer app={app} isMobile={isMobile} embed={embed} ws={ws} />
  ) : (
    <Stack container spacing={2}>
      {!embed && (
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
                href={app.logo ? "/" : "https://trypromptly.com"}
                target="_blank"
                rel="noreferrer"
              >
                <img
                  src={app.logo || logo}
                  alt="Promptly"
                  style={{ height: 30 }}
                />
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
              {app.is_shareable && (
                <TwitterShareButton
                  url={window.location.href}
                  title={`Check out ${app?.name} on Promptly!\n\n`}
                  via={"TryPromptly"}
                  hashtags={["NoCodeAI"]}
                >
                  <TwitterIcon size={30} round={true} />
                </TwitterShareButton>
              )}
            </Toolbar>
          </Container>
        </AppBar>
      )}
      <Box sx={{ justifyContent: "center" }}>{headless && <p></p>}</Box>
      {error && (
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
          <h4>{error}</h4>
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
      )}
      <Box>
        {app?.type?.slug === "web" && <WebAppRenderer app={app} ws={ws} />}
        {app?.type?.slug === "text-chat" && (
          <WebChatRender app={app} isMobile={isMobile} ws={ws} />
        )}
        {app?.type?.slug === "agent" && (
          <AgentRenderer app={app} isMobile={isMobile} ws={ws} />
        )}
      </Box>
      <Box
        sx={{
          justifyContent: "center",
          textAlign: "center",
          bottom: "0px",
          margin: "0 auto",
          paddingTop: "10px",
        }}
      >
        {headless &&
          (app.has_footer ||
            !process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT) && (
            <Typography sx={{ textAlign: "center" }} variant="caption">
              Powered by{" "}
              <a
                href="https://trypromptly.com"
                target="_blank"
                rel="noreferrer"
              >
                Promptly
              </a>
            </Typography>
          )}
      </Box>
    </Stack>
  );
}

export default AppRenderPage;
