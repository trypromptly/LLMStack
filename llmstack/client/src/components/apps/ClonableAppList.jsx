import React, { useEffect, useState } from "react";
import {
  Alert,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { axios } from "../../data/axios";
import { AppNameDialog } from "./AppNameDialog";

export function ClonableAppList() {
  const [cloneableApps, setCloneableApps] = useState([]);
  const [openNameDialog, setOpenNameDialog] = useState(false);
  const [app, setApp] = useState({});
  const [appName, setAppName] = useState("Untitled");
  const navigate = useNavigate();

  const createApp = () => {
    const payload = {
      ...app,
      name: appName || app.name || "Untitled",
      app_type: app.type.id,
    };
    payload.processors = payload.processors.map((processor) => ({
      api_backend: processor.api_backend.id,
      config: processor.config,
      input: processor.input,
    }));
    axios()
      .post("/api/apps", payload)
      .then((response) => {
        const appID = response.data.uuid;
        navigate(`/apps/${appID}`);
      });
  };

  useEffect(() => {
    axios()
      .get("/api/apps/clone")
      .then((response) => {
        setCloneableApps(response.data);
      });
  }, [setCloneableApps]);

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
      <AppNameDialog
        appName={appName}
        setAppName={setAppName}
        createApp={createApp}
        open={openNameDialog}
        setOpen={setOpenNameDialog}
        preText={
          app?.is_published && (
            <Alert severity="info">
              Check out{" "}
              <a
                href={`https://trypromptly.com/app/${app?.published_uuid}`}
                target="_blank"
                rel="noreferrer"
              >
                {app.name}
              </a>{" "}
              published app by clicking{" "}
              <a
                href={`https://trypromptly.com/app/${app?.published_uuid}`}
                target="_blank"
                rel="noreferrer"
              >
                here
              </a>
            </Alert>
          )
        }
      />
      {cloneableApps.map((app, index) => (
        <div
          key={index}
          style={{ maxWidth: "300px", cursor: "pointer" }}
          onClick={() => {
            setApp(app);
            setAppName(app.name);
            setOpenNameDialog(true);
          }}
        >
          <Card
            sx={{
              width: 200,
              height: 150,
              display: "flex",
              justifyContent: "center",
              alignItems: "baseline",
            }}
          >
            <CardContent>
              <Stack direction="column" spacing={1}>
                <Chip
                  label={app.type.name}
                  size="small"
                  style={{
                    backgroundColor: "#fff2bca3",
                    fontFamily: "Lato, sans-serif",
                  }}
                />
                <Typography
                  variant="subtitle1"
                  color="text.secondary"
                  style={{ fontFamily: "Lato, sans-serif" }}
                >
                  {app.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {app.description || app.type.description}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </div>
      ))}
    </div>
  );
}
