import { Box } from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { useRecoilValue } from "recoil";
import { appsState } from "../../data/atoms";
import { AppSelector } from "../apps/AppSelector";
import ThemedJsonForm from "../ThemedJsonForm";
import FrequencyPickerWidget from "./FrequencyPickerWidget";

const SCHEMA = {
  properties: {
    job_name: {
      type: "string",
      title: "Job Name",
    },
    application: {
      type: "string",
      title: "Application",
      widget: "appselect",
    },
    frequency: {
      type: "string",
      title: "Frequency",
      widget: "frequencyPicker",
    },
  },
};

const UI_SCHEMA = {
  "ui:order": ["job_name", "application", "frequency"],
  job_name: {
    "ui:description": "Enter a name for this job.",
  },
  application: {
    "ui:description": "Application to run with this job.",
    "ui:widget": "appselect",
  },
  frequency: {
    "ui:description": "Select a frequency to run the application.",
    "ui:widget": "frequencyPicker",
  },
};

export default function AddAppRunScheduleConfigForm(props) {
  const publishedApps = (useRecoilValue(appsState) || []).filter(
    (app) => app.published_uuid,
  );

  return (
    <Box sx={{ width: "95%", margin: "5px" }}>
      <ThemedJsonForm
        disableAdvanced={true}
        schema={SCHEMA}
        validator={validator}
        uiSchema={{
          ...UI_SCHEMA,
          ...{
            "ui:submitButtonOptions": {
              norender: true,
            },
          },
        }}
        formData={props.value}
        onChange={({ formData }) => {
          props.onChange({
            ...formData,
            appDetail: publishedApps.find(
              (app) => app.published_uuid === formData?.application,
            ),
            frequencyObj: formData?.frequency
              ? JSON.parse(formData?.frequency || "{}")
              : null,
          });
        }}
        widgets={{
          appselect: (localProps) => {
            return (
              <AppSelector
                {...localProps}
                apps={publishedApps}
                value={localProps.value}
              />
            );
          },
          frequencyPicker: (localProps) => {
            return (
              <FrequencyPickerWidget
                {...localProps}
                value={localProps.value}
                id="frequency-picker"
              />
            );
          },
        }}
      />
    </Box>
  );
}
