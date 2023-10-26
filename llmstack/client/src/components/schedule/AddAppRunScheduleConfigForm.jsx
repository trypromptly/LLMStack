import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { AppSelector } from "../apps/AppSelector";
import FrequencyPickerWidget from "./FrequencyPickerWidget";
import { useRecoilValue } from "recoil";
import { appsState } from "../../data/atoms";

const SCHEMA = {
  properties: {
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
  "ui:order": ["application", "frequency"],
  application: {
    "ui:description": "Select an application to run.",
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
    <ThemedJsonForm
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
            ? JSON.parse(formData?.frequency)
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
            <FrequencyPickerWidget {...localProps} value={localProps.value} />
          );
        },
      }}
    />
  );
}
