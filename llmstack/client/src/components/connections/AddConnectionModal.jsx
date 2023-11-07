import { useEffect, useState } from "react";
import {
  Alert,
  AlertTitle,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";
import { useRecoilValue } from "recoil";
import validator from "@rjsf/validator-ajv8";
import { Ws } from "../../data/ws";
import { connectionTypesState } from "../../data/atoms";
import { enqueueSnackbar } from "notistack";
import ThemedJsonForm from "../ThemedJsonForm";
import RemoteBrowser from "./RemoteBrowser";
import { useRecoilCallback } from "recoil";
import { axios } from "../../data/axios";
import { connectionsState } from "../../data/atoms";

function AddConnectionModal({ open, onCancelCb, onSaveCb, connection }) {
  const connectionTypes = useRecoilValue(connectionTypesState);
  const [connectionType, setConnectionType] = useState(
    connectionTypes[0] || "",
  );
  const [connectionName, setConnectionName] = useState(connection?.name || "");
  const [connectionDescription, setConnectionDescription] = useState(
    connection?.description || "",
  );
  const [configFormData, setConfigFormData] = useState(
    connection?.configuration || {},
  );
  const [localConnection, setLocalConnection] = useState(connection || {});
  const [validationErrors, setValidationErrors] = useState([]);
  const [connectionActive, setConnectionActive] = useState(false);
  const [isRemoteBrowser, setIsRemoteBrowser] = useState(false);
  const [remoteBrowserWsUrl, setRemoteBrowserWsUrl] = useState("");
  const [remoteBrowserTimeout, setRemoteBrowserTimeout] = useState(10);
  const [connectionWs, setConnectionWs] = useState(null);

  const reloadConnections = useRecoilCallback(({ set }) => () => {
    axios()
      .get("/api/connections")
      .then((res) => {
        set(connectionsState, res.data);
      })
      .catch((err) => {
        enqueueSnackbar("Error loading connections", {
          variant: "error",
        });
      });
  });

  const validateForm = () => {
    let errors = [];
    if (!connectionName) {
      errors.push("Connection name is required");
    }

    if (!connectionType) {
      errors.push("Connection type is required");
    }

    if (Object.keys(configFormData).length === 0) {
      errors.push("Configuration is required");
    }

    if (errors.length > 0) {
      setValidationErrors(errors);
      return false;
    }

    return true;
  };

  const handleCloseCb = () => {
    setConnectionName("");
    setConnectionDescription("");
    setConfigFormData({});
    onCancelCb();
  };

  const handleSaveCb = (conn) => {
    if (!validateForm()) {
      return;
    }

    onSaveCb(conn).then((res) => {
      setConnectionName("");
      setConnectionDescription("");
      setConfigFormData({});
      setLocalConnection({});

      onCancelCb();
    });
  };

  const testConnection = (conn) => () => {
    if (!validateForm()) {
      return;
    }

    // Save connection before testing
    onSaveCb(conn).then((res) => {
      setLocalConnection(res);

      if (res.id) {
        const ws = new Ws(
          `${window.location.protocol === "https:" ? "wss" : "ws"}://${
            process.env.NODE_ENV === "development"
              ? process.env.REACT_APP_API_SERVER || "localhost:9000"
              : window.location.host
          }/ws/connections/${res.id}/activate`,
        );

        if (ws) {
          setConnectionWs(ws);
          ws.setOnMessage((evt) => {
            const message = JSON.parse(evt.data);

            if (message.event === "success") {
              enqueueSnackbar("Connection test successful", {
                variant: "success",
              });
              setConnectionActive(true);
              ws.close();
              onCancelCb();
              reloadConnections();
            }

            if (message.event === "error") {
              enqueueSnackbar(
                `Connection test failed${
                  message.error ? `: ${message.error}` : ""
                }`,
                {
                  variant: "error",
                },
              );
              ws.close();
            }

            if (
              message.event === "output" &&
              message.output &&
              message.output.ws_url
            ) {
              console.log(message);
              setRemoteBrowserWsUrl(message.output.ws_url);
              setRemoteBrowserTimeout(message.output.timeout);
              setIsRemoteBrowser(true);
            }
          });

          ws.send(
            JSON.stringify({
              event: "activate",
            }),
          );
        }
      }
    });
  };

  useEffect(() => {
    setTimeout(() => setConfigFormData(connection?.configuration || {}), 500);
  }, [connection]);

  useEffect(() => {
    if (!open) {
      return;
    }

    setValidationErrors([]);
  }, [open, connectionName, connectionDescription, configFormData]);

  useEffect(() => {
    if (!open) {
      return;
    }

    setLocalConnection(connection || {});
    setConnectionName(connection?.name || "");
    setConnectionDescription(connection?.description || "");
    setConfigFormData(connection?.configuration || {});

    if (connection) {
      setConnectionType(
        connectionTypes.find(
          (t) =>
            t.provider_slug === connection?.provider_slug &&
            t.slug === connection?.connection_type_slug,
        ),
      );
    } else {
      setConnectionType(connectionTypes[0] || "");
    }
  }, [connection, connectionTypes, open]);

  return (
    <Dialog open={open} onClose={handleCloseCb} fullWidth>
      <DialogTitle>{`${connection ? "Edit" : "Add"} Connection`}</DialogTitle>
      <DialogContent>
        {validationErrors.length > 0 && (
          <Alert severity="error">
            <AlertTitle>Errors in the form</AlertTitle>
            <ul>
              {validationErrors.map((e, index) => (
                <li key={index}>{e}</li>
              ))}
            </ul>
          </Alert>
        )}
        <br />
        <FormControl fullWidth sx={{ gap: "10px" }}>
          <TextField
            label="Name"
            value={connectionName}
            placeholder="Enter a name for your connection"
            onChange={(e) => {
              setConnectionName(e.target.value);
              setLocalConnection({
                ...localConnection,
                name: e.target.value,
              });
            }}
            variant="outlined"
          />
          <TextField
            label="Description"
            placeholder="Enter a description for your connection"
            value={connectionDescription}
            onChange={(e) => {
              setConnectionDescription(e.target.value);
              setLocalConnection({
                ...localConnection,
                description: e.target.value,
              });
            }}
            multiline
            variant="outlined"
          />
        </FormControl>
        <FormControl fullWidth sx={{ margin: "20px 0 20px 0" }}>
          <InputLabel id="connection-type-label">Connection Type</InputLabel>
          <Select
            label="Connection Type"
            labelId="connection-type-label"
            value={
              connectionType
                ? `${connectionType?.provider_slug}:${connectionType?.slug}`
                : ""
            }
            onChange={(e) =>
              setConnectionType(
                connectionTypes.find(
                  (t) =>
                    t.provider_slug === e.target.value.split(":")[0] &&
                    t.slug === e.target.value.split(":")[1],
                ),
              )
            }
          >
            {connectionTypes
              .map((t) => {
                return { label: t.name, value: `${t.provider_slug}:${t.slug}` };
              })
              .map((option, index) => (
                <MenuItem key={index} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
          </Select>
        </FormControl>
        <InputLabel>Configuration</InputLabel>
        <ThemedJsonForm
          schema={
            connectionType?.config_schema || {
              type: "object",
              properties: {},
            }
          }
          validator={validator}
          uiSchema={{
            ...(connectionType?.config_ui_schema || {}),
            ...{
              "ui:submitButtonOptions": {
                norender: true,
              },
              "ui:DescriptionFieldTemplate": () => null,
              "ui:TitleFieldTemplate": () => null,
            },
          }}
          formData={configFormData}
          onChange={({ formData }) => {
            setConnectionActive(false);
            setConfigFormData(formData);
            setLocalConnection({
              ...localConnection,
              configuration: formData,
            });
          }}
        />
        {isRemoteBrowser && (
          <RemoteBrowser
            wsUrl={remoteBrowserWsUrl}
            timeout={remoteBrowserTimeout}
            onClose={() => {
              console.log("Closing remote browser");
              setIsRemoteBrowser(false);
              setRemoteBrowserWsUrl(null);
              connectionWs.send(
                JSON.stringify({
                  event: "input",
                  input: "terminate",
                }),
              );
            }}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCloseCb}>Cancel</Button>
        {!connectionActive && (
          <Button
            onClick={testConnection({
              ...connection,
              ...localConnection,
              ...{
                provider_slug: connectionType?.provider_slug,
                connection_type_slug: connectionType?.slug,
              },
            })}
            variant="contained"
          >
            Test Connection
          </Button>
        )}
        {connectionActive && (
          <Button
            onClick={() =>
              handleSaveCb({
                ...connection,
                ...localConnection,
                ...{
                  provider_slug: connectionType?.provider_slug,
                  connection_type_slug: connectionType?.slug,
                },
              })
            }
            variant="contained"
          >
            Save
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

export default AddConnectionModal;
