import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import * as React from "react";
import AceEditor from "react-ace";
import { useRecoilState } from "recoil";
import { Empty as EmptyComponent } from "../components/form/Empty";
import { endpointConfigValueState } from "../data/atoms";
import ThemedJsonForm from "./ThemedJsonForm";

import "ace-builds/src-noconflict/mode-json";
import "ace-builds/src-noconflict/theme-chrome";

export function ThemedForm(props) {
  const [data, setData] = useRecoilState(endpointConfigValueState);
  return (
    <ThemedJsonForm
      schema={props.schema}
      uiSchema={props.uiSchema}
      formData={data}
      onChange={({ formData }) => {
        setData(formData);
      }}
      validator={validator}
    />
  );
}

export function ThemedJsonEditor() {
  const [data, setData] = useRecoilState(endpointConfigValueState);

  return (
    <AceEditor
      mode="json"
      theme="chrome"
      value={JSON.stringify(data, null, 2)}
      onChange={(data) => {
        setData(JSON.parse(data));
      }}
      editorProps={{ $blockScrolling: true }}
      setOptions={{
        useWorker: false,
        showGutter: false,
      }}
    />
  );
}

export default function ConfigForm(props) {
  const [value, setValue] = React.useState("form");

  let schema = props.schema ? JSON.parse(JSON.stringify(props.schema)) : {};

  if (props?.schema?.title) {
    schema.title = null;

    schema.description = null;
  }

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setValue(newValue);
            }}
            aria-label="Config form tabs"
          >
            <Tab label="Config Form" value="form" />
            <Tab label="JSON" value="json" />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          {Object.keys(props.schema).length === 0 ? (
            <EmptyComponent {...props} />
          ) : (
            <ThemedForm schema={schema} uiSchema={props.uiSchema} />
          )}
        </TabPanel>
        <TabPanel value="json" sx={{ padding: "4px" }}>
          {Object.keys(props.schema).length === 0 ? (
            <EmptyComponent {...props} />
          ) : (
            <ThemedJsonEditor {...props} />
          )}
        </TabPanel>
      </TabContext>
    </Box>
  );
}
