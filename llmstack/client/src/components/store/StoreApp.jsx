import React, { useState, useEffect } from "react";
import { Box, Card, Chip, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import Grid from "@mui/material/Unstable_Grid2";
import { useRecoilValue } from "recoil";
import { AppRenderer } from "../apps/renderer/AppRenderer";
import { Ws } from "../../data/ws";
import { storeAppState } from "../../data/atoms";

const AppIcon = styled("img")({
  width: 80,
  height: 80,
  margin: "1em 0.5em",
  borderRadius: 1,
});

function StoreAppHeader({ name, icon, username, description, categories }) {
  return (
    <Card sx={{ marginLeft: 2, marginTop: 1 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          textAlign: "left",
          pl: 1,
          pb: 1,
        }}
      >
        <AppIcon src={icon} alt={name} />
        <Box sx={{ padding: 2 }}>
          <Typography
            component="div"
            color="text.primary"
            sx={{ fontSize: 24, fontWeight: 600 }}
          >
            {name}
          </Typography>
          <Typography color="text.secondary">
            by <b>{username}</b>
          </Typography>
          <Box sx={{ mt: 1, mb: 1 }}>
            {categories &&
              categories.map((category) => (
                <Chip label={category} size="small" />
              ))}
          </Box>
        </Box>
      </Box>
      <Box sx={{ textAlign: "left", ml: 2, mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>
    </Card>
  );
}

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
    <Box>
      <Grid container spacing={0} direction={"column"}>
        <Grid>
          <StoreAppHeader
            name={storeApp.name}
            icon={storeApp.icon}
            username={storeApp.username}
            description={storeApp.description}
            categories={storeApp.categories}
          />
        </Grid>
        <Grid>
          <AppRenderer app={storeApp} ws={ws} />
        </Grid>
      </Grid>
    </Box>
  );
}
