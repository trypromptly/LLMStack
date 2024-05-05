import { useRecoilValue } from "recoil";
import { appsState } from "../../data/atoms";
import { MenuItem, Select, Stack } from "@mui/material";
import { useEffect, useState } from "react";
import validator from "@rjsf/validator-ajv8";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import ThemedJsonForm from "../ThemedJsonForm";

export default function PromptlyAppSelectorWidget(props) {
  const { value, onChange } = props;
  const apps = useRecoilValue(appsState);
  const published_apps = apps.filter((app) => app.is_published);

  const [selectedApp, setSelectedApp] = useState(null);
  const [inputSchema, setInputSchema] = useState({});
  const [inputUiSchema, setInputUiSchema] = useState({});
  const [jsonValue, setJsonValue] = useState({});

  useEffect(() => {
    try {
      setJsonValue(JSON.parse(value));
    } catch (e) {
      console.error(e);
    }
  }, [value]);

  useEffect(() => {
    if (jsonValue) {
      const selectedApp = published_apps.find(
        (app) => app.published_uuid === jsonValue?.promptly_app_published_uuid,
      );
      setSelectedApp(selectedApp);
    }
  }, [jsonValue]);

  useEffect(() => {
    if (selectedApp) {
      if (selectedApp.data.input_fields) {
        const { schema, uiSchema } = getJSONSchemaFromInputFields(
          selectedApp.data.input_fields,
        );
        setInputSchema(schema);
        setInputUiSchema(uiSchema);
      }
    }
  }, [selectedApp]);

  return (
    <Stack>
      <Select
        labelId="app-select-label"
        id="app-select"
        value={jsonValue?.promptly_app_published_uuid || ""}
        label="Select an application"
        onChange={(event) => {
          const appData = published_apps.find(
            (app) => app.published_uuid === event.target.value,
          );
          props.onChange(
            JSON.stringify({
              promptly_app_published_uuid: event.target.value,
              promptly_app_input_fields: appData?.data.input_fields || [],
              promptly_app_version: appData?.version || 0,
              promptly_app_uuid: appData?.uuid || "",
            }),
          );
        }}
        variant="filled"
        sx={{ lineHeight: "0.5em" }}
      >
        {published_apps.map((app) => (
          <MenuItem key={app.published_uuid} value={app.published_uuid}>
            {app.name}
          </MenuItem>
        ))}
      </Select>
      <ThemedJsonForm
        schema={inputSchema}
        uiSchema={inputUiSchema}
        formData={jsonValue?.input || {}}
        onChange={({ formData }) => {
          onChange(
            JSON.stringify({
              promptly_app_published_uuid:
                jsonValue.promptly_app_published_uuid,
              promptly_app_input_fields: jsonValue.promptly_app_input_fields,
              promptly_app_version: jsonValue.promptly_app_version,
              promptly_app_uuid: jsonValue.promptly_app_uuid,
              input: formData,
            }),
          );
        }}
        validator={validator}
        disableAdvanced={true}
      />
    </Stack>
  );
}
