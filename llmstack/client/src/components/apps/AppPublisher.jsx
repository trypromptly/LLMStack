import PersonAddIcon from "@mui/icons-material/PersonAdd";
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  TextField,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import { profileFlagsSelector } from "../../data/atoms";
import { axios } from "../../data/axios";

const shareDialogStyles = {
  width: "100%",
  maxWidth: 500,
  margin: "auto",
  "& .MuiButtonBase-root": {
    "&.MuiButton-root": {
      textTransform: "none",
    },
  },
};

function PublishModalInternal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility = null,
  setReadAccessibleBy = null,
  setWriteAccessibleBy = null,
  editSharing = false,
}) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [done, setDone] = useState(false);
  const [visibility, setVisibility] = useState(app?.visibility);
  const [accessibleByEmail, setAccessibleByEmail] = useState("");
  const [accessibleByAccess, setAccessibleByAccess] = useState(0);
  const [accessibleBy, setAccessibleBy] = useState(
    (
      app?.read_accessible_by?.map((entry) => ({
        email: entry,
        access: 0,
      })) || []
    ).concat(
      app?.write_accessible_by?.map((entry) => ({
        email: entry,
        access: 1,
      })),
    ) || [],
  );
  const profileFlags = useRecoilValue(profileFlagsSelector);

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
        read_accessible_by: accessibleBy
          .filter((entry) => entry.access === 0)
          .map((entry) => entry.email),
        write_accessible_by: accessibleBy
          .filter((entry) => entry.access === 1)
          .map((entry) => entry.email),
      })
      .then(() => {
        setIsPublished(true);
        setDone(true);
        if (setAppVisibility) {
          setAppVisibility(visibility);
        }
        if (setReadAccessibleBy) {
          setReadAccessibleBy(
            accessibleBy.filter((entry) => entry.access === 0),
          );
        }
        if (setWriteAccessibleBy) {
          setWriteAccessibleBy(
            accessibleBy.filter((entry) => entry.access === 1),
          );
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
    <Dialog
      open={show}
      onClose={() => {
        setShow(false);
        setDone(false);
      }}
      sx={shareDialogStyles}
    >
      <DialogTitle>{editSharing ? "App Sharing" : "Publish App"}</DialogTitle>
      <DialogContent>
        {done && <p>App {editSharing ? "saved" : "published"} successfully!</p>}
        {!done && (
          <Box>
            <p>
              Choose a visiblity level for this app. This setting can be changed
              later.
            </p>
            <p></p>
            <FormControl fullWidth>
              <Select
                id="visibility"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value)}
                size="small"
                renderValue={(value) =>
                  visibilityOptions.find((option) => option.value === value)
                    ?.label
                }
              >
                {visibilityOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}&nbsp;
                    <br />
                    <small>{option.description}</small>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <p></p>
            <TableContainer
              sx={{
                ".MuiTableCell-root": {
                  padding: "2px",
                },
                ".MuiTable-root": {
                  marginTop: "10px",
                },
              }}
            >
              <p>Users with access:</p>
              <Stack direction="row" spacing={1}>
                <TextField
                  label="Invite by email"
                  value={accessibleByEmail}
                  onChange={(e) => setAccessibleByEmail(e.target.value)}
                  size="small"
                  disabled={
                    visibilityOptions.find((option) => option.value === 0) ===
                    undefined
                  }
                />
                <Select
                  id="access-permission"
                  size="small"
                  value={accessibleByAccess}
                  onChange={(e) => setAccessibleByAccess(e.target.value)}
                  renderValue={(value) =>
                    value === 0 ? "Viewer" : "Collaborator"
                  }
                >
                  {accessPermissionOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
                <Button
                  variant="outlined"
                  onClick={() => {
                    // Verify email is valid
                    if (
                      !accessibleByEmail.match(
                        /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
                      )
                    ) {
                      enqueueSnackbar("Invalid email address", {
                        variant: "error",
                      });
                      return;
                    }
                    const newAccessibleBy = [...accessibleBy];
                    newAccessibleBy.push({
                      email: accessibleByEmail,
                      access: accessibleByAccess,
                    });
                    setAccessibleBy(newAccessibleBy);
                    setAccessibleByEmail("");
                    setAccessibleByAccess(0);
                  }}
                  startIcon={<PersonAddIcon />}
                >
                  Add
                </Button>
              </Stack>
              <Divider sx={{ marginTop: 2 }} />
              <Table>
                <TableBody>
                  {accessibleBy.map((entry, index) => (
                    <TableRow key={index}>
                      <TableCell>{entry.email}</TableCell>
                      <TableCell>
                        <FormControl>
                          <Select
                            id="access-permission"
                            size="small"
                            value={entry.access}
                            onChange={(e) => {
                              const newAccessibleBy = [...accessibleBy];

                              // Remove user from list
                              if (e.target.value === -1) {
                                newAccessibleBy.splice(index, 1);
                                setAccessibleBy(newAccessibleBy);
                                return;
                              }

                              newAccessibleBy[index].access = e.target.value;
                              setAccessibleBy(newAccessibleBy);
                            }}
                            renderValue={(value) =>
                              value === 0 ? "Viewer" : "Collaborator"
                            }
                            variant="standard"
                          >
                            {accessPermissionOptions
                              .concat([
                                {
                                  label: "Remove",
                                  value: -1,
                                  description: "Remove this user from the list",
                                },
                              ])
                              .map((option) => (
                                <MenuItem
                                  key={option.value}
                                  value={option.value}
                                >
                                  {option.label}&nbsp;
                                  <br />
                                  <small>{option.description}</small>
                                </MenuItem>
                              ))}
                          </Select>
                        </FormControl>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button
          onClick={() => {
            setShow(false);
            setDone(false);
          }}
        >
          Cancel
        </Button>
        <Button onClick={publishApp} variant="contained">
          {isPublishing ? (
            <CircularProgress />
          ) : done ? (
            <a
              href={`/app/${app.published_uuid}`}
              target="_blank"
              rel="noreferrer"
              style={{ color: "white", textDecoration: "none" }}
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
  setReadAccessibleBy,
  setWriteAccessibleBy,
}) {
  return (
    <PublishModalInternal
      show={show}
      setShow={setShow}
      app={app}
      setIsPublished={setIsPublished}
      setAppVisibility={setAppVisibility}
      setReadAccessibleBy={setReadAccessibleBy}
      setWriteAccessibleBy={setWriteAccessibleBy}
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
    <Dialog open={show} onClose={() => setShow(false)} sx={shareDialogStyles}>
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
        <Button onClick={unpublishApp} variant="contained">
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
