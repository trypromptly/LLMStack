import React, { useState, useEffect } from "react";
import { Box } from "@mui/material";
import Grid from "@mui/material/Unstable_Grid2";
import { useRecoilValue } from "recoil";
import { AppRenderer } from "../apps/renderer/AppRenderer";
import { Ws } from "../../data/ws";
import { storeAppState } from "../../data/atoms";
import StoreAppHeader from "./StoreAppHeader";

export default function StoreApp({ appSlug }) {
  const storeApp = useRecoilValue(storeAppState(appSlug));
  const [ws, setWs] = useState(null);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    if (!ws) {
      setWs(new Ws(`${wsUrlPrefix}/store/apps/${appSlug}`));
    }
  }, [appSlug, ws, wsUrlPrefix]);

  if (!storeApp) {
    return <Box>Loading...</Box>;
  }

  return (
    <Grid container spacing={1} direction={"column"} sx={{ height: "100%" }}>
      <Grid>
        <StoreAppHeader
          name={storeApp.name}
          icon={storeApp.icon128}
          username={storeApp.username}
          description={storeApp.description}
          categories={storeApp.categories}
        />
      </Grid>
      <Grid
        sx={{
          flex: 1,
          padding: 4,
          paddingBottom: 0,
          height: 0,
          overflow: "auto",
        }}
      >
        <AppRenderer app={storeApp} ws={ws} />
      </Grid>
    </Grid>
  );
}
