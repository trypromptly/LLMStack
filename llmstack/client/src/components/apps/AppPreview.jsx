import { Box } from "@mui/material";
import { useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../../data/atoms";
import { Ws } from "../../data/ws";
import { AgentRenderer } from "./AgentRenderer";
import { WebAppRenderer } from "./WebAppRenderer";
import { WebChatRender } from "./WebChatRender";

export function AppPreview(props) {
  const { app } = props;
  const [ws, setWs] = useState(null);
  const isMobile = useRecoilValue(isMobileState);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    if (!ws) {
      setWs(new Ws(`${wsUrlPrefix}/apps/${app?.uuid}/preview`));
    }
  }, [app, ws, wsUrlPrefix]);

  return (
    <Box>
      {app?.type?.slug === "web" && <WebAppRenderer app={app} ws={ws} />}
      {app?.type?.slug === "text-chat" && (
        <WebChatRender app={app} isMobile={isMobile} ws={ws} />
      )}
      {app?.type?.slug === "agent" && (
        <AgentRenderer app={app} isMobile={isMobile} ws={ws} />
      )}
    </Box>
  );
}
