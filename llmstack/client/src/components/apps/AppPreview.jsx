import { lazy, useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../../data/atoms";
import { Ws } from "../../data/ws";

const AppRenderer = lazy(() => import("./renderer/AppRenderer"));

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

  return <AppRenderer isMobile={isMobile} app={app} ws={ws} />;
}
