import { useEffect } from "react";
import ConnectionSelector from "../connections/ConnectionSelector";
import { connectionsState } from "../../data/atoms";
import { useRecoilValue } from "recoil";
import { Button, Box, TextField } from "@mui/material";

function GdriveFilePicker(props) {
  useEffect(() => {
    if (window.gapi) {
      window.gapi.load("picker");
    }
  }, []);

  return (
    <Box>
      {props?.connection &&
        props?.connection?.connection_type_slug === "google_oauth2" && (
          <Box>
            <Button
              onClick={() => {
                const view = new window.google.picker.View(
                  window.google.picker.ViewId.DOCS,
                );
                const picker = new window.google.picker.PickerBuilder()
                  .enableFeature(window.google.picker.Feature.NAV_HIDDEN)
                  .addView(view)
                  .setOAuthToken(props.connection.configuration.token)
                  .setCallback((data) => {
                    if (data.action === window.google.picker.Action.PICKED) {
                      console.log(data.docs);
                      props.onChange(data.docs);
                    }
                  })
                  .build();
                picker.setVisible(true);
                console.log(props.connection.configuration.token);
                console.log(picker);
              }}
            >
              Select
            </Button>
            <TextField
              disabled
              variant="standard"
              value={(props?.value || []).map((f) => f.name).join(", ")}
            />
          </Box>
        )}
    </Box>
  );
}
export default function GdriveFileSelector(props) {
  const connections = useRecoilValue(connectionsState);

  return (
    <div>
      <ConnectionSelector
        value={props?.value ? JSON.parse(props.value)?.connection_id : null}
        onChange={(value) => {
          props.onChange(
            JSON.stringify({
              connection_id: value,
            }),
          );
        }}
      />
      <GdriveFilePicker
        connection={
          connections.find(
            (c) =>
              c.id ===
              (props.value ? JSON.parse(props.value)?.connection_id : null),
          ) || null
        }
        value={props?.value ? JSON.parse(props.value)?.files : null}
        onChange={(value) => {
          props.onChange(
            JSON.stringify({
              connection_id: props.value
                ? JSON.parse(props.value)?.connection_id
                : null,
              files: value,
            }),
          );
        }}
      />
    </div>
  );
}
