import ReactGA from "react-ga4";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { axios } from "../data/axios";
import { Ws } from "../data/ws";

import {
  PublishedApp,
  PublishedAppChatEmbed,
  PublishedAppWebEmbed,
} from "../components/apps/Published";
import { isLoggedInState, isMobileState } from "../data/atoms";

function PublishedAppPage() {
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
      (process.env.REACT_APP_GA_MEASUREMENT_IDS || "G-WV60HC9CHD")
        .split(",")
        .map((measurementId) => {
          return {
            trackingId: measurementId,
            gaOptions: {
              cookieFlags: "SameSite=None;Secure",
            },
          };
        }),
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

  if (embed && chatBubble) {
    return (
      <PublishedAppChatEmbed
        ws={ws}
        app={app}
        error={error}
        isLoggedIn={isLoggedIn}
        isMobile={isMobile}
      />
    );
  } else if (embed) {
    return (
      <PublishedAppWebEmbed
        ws={ws}
        app={app}
        error={error}
        isLoggedIn={isLoggedIn}
        isMobile={isMobile}
      />
    );
  }

  return (
    <PublishedApp
      ws={ws}
      app={app}
      error={error}
      isLoggedIn={isLoggedIn}
      isMobile={isMobile}
    />
  );
}

export default PublishedAppPage;
