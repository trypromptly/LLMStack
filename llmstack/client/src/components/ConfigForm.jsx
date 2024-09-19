import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { useState } from "react";
import AceEditor from "react-ace";
import { Empty as EmptyComponent } from "../components/form/Empty";
import ThemedJsonForm from "./ThemedJsonForm";

import "ace-builds/src-noconflict/mode-json";
import "ace-builds/src-noconflict/theme-chrome";

export function ThemedForm(props) {
  const { config, setConfig } = props;

  return (
    <ThemedJsonForm
      schema={props.schema}
      uiSchema={props.uiSchema}
      formData={config}
      onChange={({ formData }) => {
        setConfig(formData);
      }}
      validator={validator}
    />
  );
}

export function ThemedJsonEditor(props) {
  const { config, setConfig } = props;

  return (
    <AceEditor
      mode="json"
      theme="chrome"
      value={JSON.stringify(config, null, 2)}
      onChange={(data) => {
        setConfig(JSON.parse(data));
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
  const { config, setConfig } = props;
  const [tabValue, setTabValue] = useState("form");

  let schema = props.schema ? JSON.parse(JSON.stringify(props.schema)) : {};

  if (props?.schema?.title) {
    schema.title = null;

    schema.description = null;
  }

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setTabValue(newValue);
            }}
            aria-label="Config form tabs"
          >
            <Tab label="Configuration" value="form" />
            <Tab label="JSON" value="json" />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          {Object.keys(props.schema).length === 0 ? (
            <EmptyComponent {...props} />
          ) : (
            <ThemedForm
              schema={schema}
              uiSchema={props.uiSchema}
              config={config}
              setConfig={setConfig}
            />
          )}
        </TabPanel>
        <TabPanel value="json" sx={{ padding: "4px" }}>
          {Object.keys(props.schema).length === 0 ? (
            <EmptyComponent {...props} />
          ) : (
            <ThemedJsonEditor config={config} setConfig={setConfig} />
          )}
        </TabPanel>
      </TabContext>
    </Box>
  );
}
