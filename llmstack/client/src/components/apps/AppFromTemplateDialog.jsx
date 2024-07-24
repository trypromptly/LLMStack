import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { appTemplateState } from "../../data/atoms";
import { axios } from "../../data/axios";
import DropzoneFileWidget from "../form/DropzoneFileWidget";

export function AppFromTemplateDialog({
  open,
  setOpen,
  appTemplateSlug,
  app,
  setApp,
}) {
  const [appName, setAppName] = useState(app?.name || "Untitled");
  const [appDescription, setAppDescription] = useState(app?.description || "");
  const [appIcon, setAppIcon] = useState(app?.icon || "");
  const appTemplate = useRecoilValue(
    appTemplateState(
      appTemplateSlug?.startsWith("_blank_") ? "_blank_" : appTemplateSlug,
    ),
  );
  const navigate = useNavigate();

  const handleClose = () => {
    setOpen(false);
  };

  const saveApp = () => {
    const payload = {
      ...(app || {}),
      name: appName,
      description: appDescription,
      icon: appIcon,
    };
    axios()
      .patch(`/api/apps/${app.uuid}`, payload)
      .then(() => {
        setApp(payload);
        setOpen(false);
      });
  };

  const createApp = () => {
    const payload = {
      ...(appTemplate.app || {}),
      name: appName || appTemplate?.name || "Untitled",
      description: appDescription || appTemplate?.description || "",
      icon: appIcon,
      app_type: appTemplate?.app?.type,
      type_slug:
        appTemplate?.app?.type_slug ||
        appTemplateSlug?.replaceAll("_blank_", ""),
      template_slug: appTemplate?.slug,
    };
    axios()
      .post("/api/apps", payload)
      .then((response) => {
        const appID = response.data.uuid;
        navigate(`/apps/${appID}`);
      });
  };

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>
        {appTemplate?.name || (app ? "Edit App" : "Create a new App")}
      </DialogTitle>
      <DialogContent>
        <Typography style={{ fontSize: "14px", color: "#555" }}>
          {appTemplate?.description}
          {appTemplate?.example_app_uuid && " Try it out "}
          {appTemplate?.example_app_uuid && (
            <a
              href={`https://trypromptly.com/app/${appTemplate?.example_app_uuid}`}
              target="_blank"
              rel="noreferrer"
            >
              here
            </a>
          )}
        </Typography>
        <Stack gap={0.5} direction="row" mt={2}>
          {appTemplate?.categories?.map((tag, index) => (
            <Chip
              key={index}
              label={tag?.name}
              variant="outlined"
              size="small"
              sx={{ borderRadius: "5px" }}
            />
          ))}
        </Stack>
        {!app && (
          <Typography
            variant="body1"
            style={{
              paddingTop: 10,
              paddingBottom: 5,
              fontSize: "16px",
            }}
          >
            To begin creating your application, please provide the following
            information.
          </Typography>
        )}
        <TextField
          autoFocus
          margin="dense"
          id="name"
          label="Name"
          type="text"
          fullWidth
          value={appName}
          required={true}
          onChange={(e) => setAppName(e.target.value)}
        />
        <TextField
          margin="dense"
          id="description"
          label="Description"
          type="text"
          fullWidth
          multiline
          minRows={3}
          placeholder="Describe your app. Markdown supported."
          value={appDescription}
          onChange={(e) => setAppDescription(e.target.value)}
        />
        <DropzoneFileWidget
          label="App Icon"
          onChange={setAppIcon}
          value={appIcon}
          multiple={false}
          schema={{
            type: "string",
            format: "data-url",
            accepts: { "image/*": [] },
          }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} sx={{ textTransform: "none" }}>
          Cancel
        </Button>
        <Button
          onClick={app ? saveApp : createApp}
          variant="contained"
          sx={{ textTransform: "none" }}
        >
          {app ? "Save" : "Create App"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
