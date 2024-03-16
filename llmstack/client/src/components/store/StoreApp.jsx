import React, { useState, useEffect } from "react";
import { Box, Button, Card, Chip, Collapse, Typography } from "@mui/material";
import {
  KeyboardDoubleArrowDownOutlined,
  KeyboardDoubleArrowUpOutlined,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import Grid from "@mui/material/Unstable_Grid2";
import { useRecoilValue } from "recoil";
import { AppRenderer } from "../apps/renderer/AppRenderer";
import { Ws } from "../../data/ws";
import { storeAppState } from "../../data/atoms";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";

const AppIcon = styled("img")({
  width: 80,
  height: 80,
  margin: "1em 0.5em",
  borderRadius: 1,
});

function StoreAppHeader({ name, icon, username, description, categories }) {
  const [expanded, setExpanded] = useState(false);

  const handleExpand = () => {
    setExpanded(!expanded);
  };

  return (
    <Card sx={{ marginLeft: 2, marginTop: 1, backgroundColor: "#edeff7" }}>
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
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <LayoutRenderer>{description}</LayoutRenderer>
        </Collapse>
        <Collapse in={!expanded} timeout="auto" unmountOnExit>
          <Typography>{description.substring(0, 200)}</Typography>
        </Collapse>
        {description.length > 200 && (
          <Button
            onClick={handleExpand}
            size="small"
            sx={{
              textTransform: "none",
              fontSize: "0.8em",
              "& .MuiButton-startIcon": {
                marginRight: "0.5em",
              },
            }}
            startIcon={
              expanded ? (
                <KeyboardDoubleArrowUpOutlined />
              ) : (
                <KeyboardDoubleArrowDownOutlined />
              )
            }
          >
            {expanded ? "Show Less" : "View More"}
          </Button>
        )}
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
    <Grid container spacing={2} direction={"column"}>
      <Grid>
        <StoreAppHeader
          name={storeApp.name}
          icon={storeApp.icon512}
          username={storeApp.username}
          description={storeApp.description}
          categories={storeApp.categories}
        />
      </Grid>
      <Grid>
        <AppRenderer app={storeApp} ws={ws} />
      </Grid>
    </Grid>
  );
}
