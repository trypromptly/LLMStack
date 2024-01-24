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
    batch_size: {
      type: "number",
      title: "Batch Size",
      default: 1,
      minimum: 1,
      maximum: 10,
    },
    use_session: {
      type: "boolean",
      title: "Use Session",
      default: false,
    },
  },
};

const UI_SCHEMA = {
  "ui:order": [
    "job_name",
    "application",
    "frequency",
    "batch_size",
    "use_session",
  ],
  job_name: {
    "ui:description": "Enter a name for this job.",
    "ui:advanced": false,
  },
  application: {
    "ui:description": "Application to run with this job.",
    "ui:widget": "appselect",
    "ui:advanced": false,
  },
  frequency: {
    "ui:description": "Select a frequency to run the application.",
    "ui:widget": "frequencyPicker",
    "ui:advanced": false,
  },
  batch_size: {
    "ui:description": "Select a batch size to run the application.",
    "ui:advanced": true,
  },
  use_session: {
    "ui:description": "Use session in batch run.",
    "ui:advanced": true,
  },
};

export default function AddAppRunScheduleConfigForm(props) {
  const publishedApps = (useRecoilValue(appsState) || []).filter(
    (app) => app.is_published,
  );

  return (
    <Box sx={{ width: "95%", margin: "5px" }}>
      <ThemedJsonForm
        disableAdvanced={false}
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
