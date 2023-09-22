import React, { useState, useEffect } from "react";
import { Card, CardContent, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { axios } from "../../data/axios";
import { AppNameDialog } from "./AppNameDialog";

export function AppTypeSelector() {
  const [appTypes, setAppTypes] = useState([]);
  const [appType, setAppType] = useState(null);
  const [appName, setAppName] = useState("Untitled");
  const [appNameDialogOpen, setAppNameDialogOpen] = useState(false);
  const navigate = useNavigate();

  const createApp = () => {
    const payload = {
      app_type: appType.id,
      name: appName || "Untitled",
      description: "New Promptly App",
      config: {},
      input_schema: {},
      app_input_schema: {},
      processors: [],
    };
    axios()
      .post("/api/apps", payload)
      .then((response) => {
        const appID = response.data.uuid;
        navigate(`/apps/${appID}`);
      });
  };

  useEffect(() => {
    axios()
      .get("/api/app_types")
      .then((response) => {
        setAppTypes(
          response.data.filter(
            (appType) => appType.slug === "web" || appType.slug === "text-chat",
          ),
        );
      });
  }, [setAppTypes]);

  return (
    <div style={{ display: "flex", gap: 15 }}>
      <AppNameDialog
        open={appNameDialogOpen}
        setOpen={setAppNameDialogOpen}
        appName={appName}
        setAppName={setAppName}
        createApp={createApp}
      />
      {appTypes.map((appType, index) => (
        <div key={index}>
          <Card
            sx={{
              width: 200,
              height: 150,
              cursor: "pointer",
            }}
            onClick={() => {
              setAppType(appType);
              setAppNameDialogOpen(true);
            }}
          >
            <CardContent>
              <Stack direction="column" spacing={1}>
                <Typography
                  variant="subtitle1"
                  color="text.secondary"
                  style={{ fontFamily: "Lato, sans-serif", fontWeight: "bold" }}
                >
                  {appType.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {appType.description}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </div>
      ))}
    </div>
  );
}
