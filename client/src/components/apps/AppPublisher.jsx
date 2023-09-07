import React, { useState } from "react";
import { profileFlagsState } from "../../data/atoms";
import { axios } from "../../data/axios";
import { useRecoilValue } from "recoil";
import { enqueueSnackbar } from "notistack";
import {
  Button,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";

function PublishModalInternal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility = null,
  editSharing = false,
}) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [done, setDone] = useState(false);
  const [visibility, setVisibility] = useState(app?.visibility);
  const [accessibleBy, setAccessibleBy] = useState(app?.accessible_by || []);
  const [accessPermission, setAccessPermission] = useState(
    app?.access_permission || 0,
  );
  const profileFlags = useRecoilValue(profileFlagsState);

  const accessPermissionOptions = [
    {
      label: "Viewer",
      value: 0,
      description: "Users can view the app",
    },
    {
      label: "Collaborator",
      value: 1,
      description: "Users can collaborate on the app",
    },
  ];

  let visibilityOptions = [];

  if (profileFlags.CAN_PUBLISH_PUBLIC_APPS || app?.visibility === 3) {
    visibilityOptions.push({
      label: "Public",
      value: 3,
      description: "Anyone can access this app",
    });
  }

  if (profileFlags.CAN_PUBLISH_UNLISTED_APPS || app?.visibility === 2) {
    visibilityOptions.push({
      label: "Unlisted",
      value: 2,
      description: "Anyone with the app's published url can access this app",
    });
  }

  if (profileFlags.CAN_PUBLISH_ORG_APPS || app?.visibility === 1) {
    visibilityOptions.push({
      label: "Organization",
      value: 1,
      description: "Only members of your organization can access this app",
    });
  }

  if (profileFlags.CAN_PUBLISH_PRIVATE_APPS || app?.visibility === 0) {
    visibilityOptions.push({
      label: "Private",
      value: 0,
      description: "Only you and the selected users can access this app",
    });
  }

  const publishApp = () => {
    if (done) {
      setShow(false);
      setDone(false);
      return;
    }

    setIsPublishing(true);
    axios()
      .post(`/api/apps/${app.uuid}/publish`, {
        visibility: visibility,
        accessible_by: accessibleBy,
        access_permission: accessPermission,
      })
      .then(() => {
        setIsPublished(true);
        setDone(true);
        if (setAppVisibility) {
          setAppVisibility(visibility);
        }
      })
      .catch((error) => {
        enqueueSnackbar(
          error.response?.data?.message || "Error publishing app",
          {
            variant: "error",
          },
        );
      })
      .finally(() => {
        setIsPublishing(false);
      });
  };

  return (
    <Dialog open={show} onClose={() => setShow(false)}>
      <DialogTitle>{editSharing ? "App Sharing" : "Publish App"}</DialogTitle>
      <DialogContent>
        {done && <p>App {editSharing ? "saved" : "published"} successfully!</p>}
        {!done && (
          <div>
            <h5>Choose who can access this App</h5>
            <FormControl style={{ width: "100%" }}>
              <InputLabel id="visibility-label">Visibility</InputLabel>
              <Select
                labelId="visibility-label"
                id="visibility"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value)}
              >
                {visibilityOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                    <br />
                    <small>{option.description}</small>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {visibility === 0 && (
              <div style={{ marginTop: 10, margin: "auto" }}>
                <p>
                  Select users who can access the app. Only users with given
                  email addresses will be able to access the app.
                </p>
                <TextField
                  label="Enter valid email addresses"
                  value={accessibleBy}
                  onChange={(e) => setAccessibleBy(e.target.value)}
                  style={{ width: "75%" }}
                />
                <FormControl style={{ width: "25%" }}>
                  <InputLabel id="access-permission-label">
                    Permissions
                  </InputLabel>
                  <Select
                    labelId="access-permission-label"
                    id="access-permission"
                    value={accessPermission}
                    onChange={(e) => setAccessPermission(e.target.value)}
                  >
                    {accessPermissionOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                        <br />
                        <small>{option.description}</small>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                &nbsp;
              </div>
            )}
          </div>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShow(false)}>Cancel</Button>
        <Button onClick={publishApp}>
          {isPublishing ? (
            <CircularProgress />
          ) : done ? (
            <a
              href={`/app/${app.published_uuid}`}
              target="_blank"
              rel="noreferrer"
            >
              View Published App
            </a>
          ) : editSharing ? (
            "Save App"
          ) : (
            "Publish App"
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function PublishModal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility,
}) {
  return (
    <PublishModalInternal
      show={show}
      setShow={setShow}
      app={app}
      setIsPublished={setIsPublished}
      setAppVisibility={setAppVisibility}
    />
  );
}

export function EditSharingModal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility,
}) {
  return (
    <PublishModalInternal
      show={show}
      setShow={setShow}
      app={app}
      setIsPublished={setIsPublished}
      setAppVisibility={setAppVisibility}
      editSharing={true}
    />
  );
}

export function UnpublishModal({ show, setShow, app, setIsPublished }) {
  const [isUnpublishing, setIsUnpublishing] = useState(false);
  const [done, setDone] = useState(false);

  const unpublishApp = () => {
    if (done) {
      setShow(false);
      setDone(false);
      return;
    }

    setIsUnpublishing(true);
    axios()
      .post(`/api/apps/${app.uuid}/unpublish`)
      .then(() => {
        setIsPublished(false);
        setDone(true);
      })
      .catch((error) => {
        enqueueSnackbar(
          error.response?.data?.message || "Error unpublishing app",
          {
            variant: "error",
          },
        );
      })
      .finally(() => {
        setIsUnpublishing(false);
      });
  };

  return (
    <Dialog open={show} onClose={() => setShow(false)}>
      <DialogTitle>Unpublish App</DialogTitle>
      <DialogContent>
        {done && <p>App unpublished successfully!</p>}
        {!done && (
          <p>
            Are you sure want to unpublish the app? This will make the app
            unaccessible to anyone it was already shared with.
          </p>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShow(false)}>Cancel</Button>
        <Button onClick={unpublishApp}>
          {isUnpublishing ? (
            <CircularProgress />
          ) : done ? (
            "Done"
          ) : (
            "Yes, Unpublish App"
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
