import React, { useCallback, useEffect, useState } from "react";
import ReactGA from "react-ga4";
import { Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import { axios } from "../../data/axios";
import { AppFromTemplateDialog } from "./AppFromTemplateDialog";

export function AppTemplatesList() {
  const [appName, setAppName] = useState("Untitled");
  const [appTemplates, setAppTemplates] = useState([]);
  const [openNameDialog, setOpenNameDialog] = useState(false);
  const [appTemplate, setAppTemplate] = useState(null);
  const { appTemplateSlug } = useParams();
  const navigate = useNavigate();

  const getAppTemplate = useCallback(
    (slug) => {
      const template = appTemplates.find(
        (appTemplate) => appTemplate.slug === slug,
      );
      if (!template) {
        return;
      }

      setAppName(template.name);

      if (template.app && template.app.processors) {
        setAppTemplate(template);
      } else {
        axios()
          .get(`/api/apps/templates/${slug}`)
          .then((response) => {
            setAppTemplate(response.data);
            setAppTemplates((prev) => {
              const newTemplates = [...prev];
              const index = newTemplates.findIndex(
                (appTemplate) => appTemplate.slug === slug,
              );
              newTemplates[index] = response.data;
              return newTemplates;
            });
          });
      }
    },
    [appTemplates],
  );

  useEffect(() => {
    if (appTemplateSlug) {
      getAppTemplate(appTemplateSlug);
      setOpenNameDialog(true);
    }
  }, [appTemplateSlug, getAppTemplate]);

  const createApp = () => {
    const payload = {
      ...(appTemplate.app || {}),
      name: appName || appTemplate?.name || "Untitled",
      app_type: appTemplate.app?.type,
      app_type_slug: appTemplate.app?.type_slug,
      template_slug: appTemplate.slug,
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
      .get("/api/apps/templates")
      .then((response) => {
        setAppTemplates(response.data);
      });
  }, [setAppTemplates]);

  return (
    <Stack gap={1}>
      <AppFromTemplateDialog
        appName={appName}
        setAppName={setAppName}
        createApp={createApp}
        open={openNameDialog}
        setOpen={setOpenNameDialog}
        appTemplate={appTemplate}
      />
      <Typography
        color="text.secondary"
        sx={{ textAlign: "left", fontSize: "16px", margin: "5px" }}
      >
        Use one of our app templates to get started quickly. You can customize
        it using our visual editor.
      </Typography>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 15 }}>
        {appTemplates.map((template, index) => (
          <div
            key={index}
            style={{ maxWidth: "300px", cursor: "pointer" }}
            onClick={() => {
              ReactGA.event({
                category: "App Template",
                action: "Select",
                label: template.slug,
                transport: "beacon",
              });

              navigate(`/apps/templates/${template.slug}`);
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
              <CardContent sx={{ padding: "10px" }}>
                <Stack direction="column" spacing={1}>
                  <Typography
                    variant="subtitle1"
                    color="text.secondary"
                    style={{
                      fontFamily: "Lato, sans-serif",
                      fontWeight: "bold",
                    }}
                  >
                    {template.name}
                  </Typography>
                  {template.app?.type_slug === "agent" && (
                    <Chip
                      label="Agent"
                      size="small"
                      style={{
                        margin: "auto",
                        padding: "5px 0",
                        borderRadius: "3px",
                        backgroundColor: "#ffdca4",
                        fontSize: "12px",
                        color: "#555",
                      }}
                    />
                  )}
                  <Typography variant="caption" color="text.secondary">
                    {template.description || template.app?.type.description}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </Stack>
  );
}
