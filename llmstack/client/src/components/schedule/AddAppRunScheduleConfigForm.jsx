import { useEffect, useState } from "react";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { AppSelector } from "../apps/AppSelector";
import FrequencyPickerWidget from "./FrequencyPickerWidget";

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
  const [formData, setFormData] = useState({});

  useEffect(() => {}, []);

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
      formData={formData}
      onChange={({ formData }) => {
        setFormData(formData);
      }}
      widgets={{
        appselect: (props) => (
          <AppSelector
            {...props}
            apps={[]}
            value={formData?.published_app_id}
            onChange={(appId) => {
              setFormData({
                ...formData,
                published_app_id: appId,
              });
            }}
          />
        ),
        frequencyPicker: (props) => (
          <FrequencyPickerWidget
            {...props}
            value={formData?.frequency}
            onChange={(frequency_obj) => {
              setFormData({
                ...formData,
                ...{ frequency: JSON.stringify(frequency_obj) },
              });
            }}
          />
        ),
      }}
    />
  );
}
