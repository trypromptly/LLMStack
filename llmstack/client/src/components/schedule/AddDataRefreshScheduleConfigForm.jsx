import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import FrequencyPickerWidget from "./FrequencyPickerWidget";
import { useRecoilValue } from "recoil";
import { dataSourcesState } from "../../data/atoms";
import { Box } from "@mui/material";
import { DataSourceSelector } from "../datasource/DataSourceSelector";
import moment from "moment";

const SCHEMA = {
  properties: {
    job_name: {
      type: "string",
      title: "Job Name",
    },
    datasource: {
      type: "string",
      title: "Datasource",
      widget: "datasource",
    },
    frequency: {
      type: "string",
      title: "Frequency",
      widget: "frequencyPicker",
    },
  },
};

const UI_SCHEMA = {
  "ui:order": ["job_name", "datasource", "frequency"],
  job_name: {
    "ui:description": "Enter a name for this job.",
  },
  datasource: {
    "ui:description": "Select a datasource to setup refresh.",
    "ui:widget": "datasource",
  },
  frequency: {
    "ui:description": "Select a frequency to run the application.",
    "ui:widget": "frequencyPicker",
  },
};

export default function AddDataRefreshScheduleConfigForm(props) {
  const dataSources = useRecoilValue(dataSourcesState);

  return (
    <Box sx={{ width: "95%", margin: "5px" }}>
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
            datasourceDetails: dataSources.find(
              (dataSource) => dataSource.uuid === formData?.datasource,
            ),
            frequencyObj: formData?.frequency
              ? JSON.parse(formData?.frequency)
              : null,
          });
        }}
        widgets={{
          datasource: (props) => (
            <DataSourceSelector multiple={false} {...props} />
          ),
          frequencyPicker: (props) => (
            <FrequencyPickerWidget
              {...props}
              value={props.value}
              minStartTime={moment().add(1, "hours")}
              maxStartTime={moment().add(1, "years")}
              id="frequency-picker"
            />
          ),
        }}
      />
    </Box>
  );
}
