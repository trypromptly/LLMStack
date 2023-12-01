import { useEffect } from "react";
import ConnectionSelector from "../connections/ConnectionSelector";
import { connectionsState } from "../../data/atoms";
import { useRecoilValue } from "recoil";
import { Button, Box, TextField } from "@mui/material";
import { axios } from "../../data/axios";

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
              variant="contained"
              onClick={() => {
                const view = new window.google.picker.View(
                  window.google.picker.ViewId.DOCS,
                );
                if (props.schema?.accepts) {
                  view.setMimeTypes(
                    Object.keys(props.schema.accepts).join(","),
                  );
                }
                axios()
                  .get(
                    `/api/connections/${props.connection.id}/get_access_token`,
                  )
                  .then((response) => {
                    const oauthToken = response.data.access_token;
                    const picker = new window.google.picker.PickerBuilder()
                      .enableFeature(window.google.picker.Feature.NAV_HIDDEN)
                      .addView(view)
                      .setOAuthToken(oauthToken)
                      .setCallback((data) => {
                        if (
                          data.action === window.google.picker.Action.PICKED
                        ) {
                          props.onChange(data.docs);
                        }
                      })
                      .build();
                    picker.setVisible(true);
                  });
              }}
            >
              Choose a file
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
        schema={props.schema}
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
