import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { axios } from "../data/axios";
import { Ws } from "../data/ws";
import { Col, Row } from "antd";
import ReactGA from "react-ga4";
import { AppBar, Box, Button, Container, Toolbar } from "@mui/material";
import { TwitterIcon, TwitterShareButton } from "react-share";
import { useRecoilValue } from "recoil";
import { isMobileState, isLoggedInState } from "../data/atoms";
import { WebChatRender } from "../components/apps/WebChatRender";
import { WebAppRenderer } from "../components/apps/WebAppRenderer";
import logo from "../assets/logo.png";

function AppRenderPage({ headless = false, publishedAppIdParam = null }) {
  const { appId, publishedAppId, embed, chatBubble } = useParams();
  const [app, setApp] = useState({});
  const [renderMode, setRenderMode] = useState(null);
  const [wsUrl, setWsUrl] = useState(null);
  const [ws, setWs] = useState(null);
  const [error, setError] = useState(null);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:8000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    ReactGA.initialize("G-WV60HC9CHD", {
      gaOptions: {
        cookieFlags: "SameSite=None;Secure",
      },
    });
  }, []);

  const isMobile = useRecoilValue(isMobileState);
  const isLoggedIn = useRecoilValue(isLoggedInState);

  useEffect(() => {
    if (publishedAppId) {
      axios()
        .get(`/api/app/${publishedAppId}`)
        .then((response) => {
          setApp(response.data);
          setRenderMode("published");
          setWsUrl(`${wsUrlPrefix}/apps/${response?.data?.uuid}`);
          document.title = `${response.data.name} | Promptly`;
          ReactGA.send({
            hitType: "pageview",
            page: window.location.href,
            title: document.title,
          });
        })
        .catch((error) => {
          setError(error?.response?.data?.message);
        });
    } else if (appId) {
      setWsUrl(`${wsUrlPrefix}/apps/${appId}`);
      axios()
        .get(`/api/apps/${appId}`)
        .then((response) => {
          setApp(response.data);
          setRenderMode("preview");
        });
    } else if (publishedAppIdParam) {
      axios()
        .get(`/api/app/${publishedAppIdParam}`)
        .then((response) => {
          setApp(response.data);
          setRenderMode("published");
          setWsUrl(`${wsUrlPrefix}/apps/${response?.data?.uuid}`);
          document.title = `${response.data.name} | Promptly`;
          ReactGA.send({
            hitType: "pageview",
            page: window.location.href,
            title: document.title,
          });
        })
        .catch((error) => {
          setError(error?.response?.data?.message);
        });
    }
  }, [appId, publishedAppId, publishedAppIdParam, setApp, wsUrlPrefix]);

  useEffect(() => {
    if (wsUrl && !wsUrl.endsWith("/ws") && !ws) {
      setWs(new Ws(wsUrl));
    }
  }, [ws, wsUrl]);

  return app?.type?.slug === "text-chat" && embed && chatBubble ? (
    <WebChatRender app={app} isMobile={isMobile} embed={embed} ws={ws} />
  ) : (
    <Col>
      {renderMode !== "preview" && !embed && (
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
      <Row style={{ justifyContent: "center" }}>{headless && <p></p>}</Row>
      {error && (
        <Row
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
              window.location.href = isLoggedIn ? "/hub" : "/login";
            }}
          >
            {isLoggedIn ? "Go To Hub" : "Login"}
          </Button>
        </Row>
      )}
      <Row>
        {app?.type?.slug === "web" && <WebAppRenderer app={app} ws={ws} />}
        {app?.type?.slug === "text-chat" && (
          <WebChatRender app={app} isMobile={isMobile} ws={ws} />
        )}
      </Row>
      <Row style={{ justifyContent: "center", bottom: "0px", marginTop: 10 }}>
        {headless && app.has_footer && (
          <p>
            Powered by{" "}
            <a href="https://trypromptly.com" target="_blank" rel="noreferrer">
              Promptly
            </a>
          </p>
        )}
      </Row>
    </Col>
  );
}

export default AppRenderPage;
