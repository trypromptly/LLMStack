import { Box, Button, Grid, Stack, Tab } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import React, { lazy, useEffect, useState, useRef, useCallback } from "react";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";
import {
  apiBackendSelectedState,
  endpointConfigValueState,
  inputValueState,
  appRunDataState,
} from "../data/atoms";
import { Messages } from "../components/apps/renderer/Messages";
import { Ws } from "../data/ws";

import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-json";
import "ace-builds/src-noconflict/theme-chrome";

const defaultPlaygroundLayout = `<pa-layout sx='{"width": "100%", "margin": "10px auto"}'>
  <pa-paper style="padding: 10px;">
    <pa-grid container="true" spacing="2" style="width: 100%">
      <pa-grid item="true" xs="12">
        <pa-workflow-output></pa-workflow-output>
      </pa-grid>
    </pa-grid>
  </pa-paper>
</pa-layout>`;

const ApiBackendSelector = lazy(
  () => import("../components/ApiBackendSelector"),
);
const ConfigForm = lazy(() => import("../components/ConfigForm"));
const InputForm = lazy(() => import("../components/InputForm"));
const LoginDialog = lazy(() => import("../components/LoginDialog"));
const AppRenderer = lazy(
  () => import("../components/apps/renderer/AppRenderer"),
);

export function ThemedJsonEditor({ data }) {
  return (
    <AceEditor
      readOnly={true}
      mode="json"
      theme="chrome"
      value={JSON.stringify(data, null, 2)}
      editorProps={{ $blockScrolling: true }}
      setOptions={{
        useWorker: false,
        showGutter: false,
      }}
    />
  );
}

function Output(props) {
  const [value, setValue] = React.useState("form");
  const [jsonOutput, setJsonOutput] = useState({});

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setValue(newValue);
            }}
            aria-label="Output form tabs"
          >
            <Tab label="Output" value="form" />
            <Tab label="JSON" value="json" />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          <AppRenderer
            app={props.app}
            isMobile={false}
            ws={props.ws}
            onEventDone={(message) => {
              setJsonOutput(message?.processor || {});
            }}
          />
        </TabPanel>
        <TabPanel value="json" sx={{ padding: "4px" }}>
          <ThemedJsonEditor data={jsonOutput} />
        </TabPanel>
      </TabContext>
    </Box>
  );
}

export default function PlaygroundPage() {
  const app = {
    name: "Playground",
    uuid: null,
    data: {
      type_slug: "playground",
      output_template: { markdown: "{{ processor | json }}" },
      config: {
        layout: defaultPlaygroundLayout,
      },
    },
  };
  const [input] = useRecoilState(inputValueState);
  const appSessionId = useRef(null);
  const messagesRef = useRef(new Messages());
  const [showLoginDialog, setShowLoginDialog] = useState(false);
  const setAppRunData = useSetRecoilState(appRunDataState);

  const apiBackendSelected = useRecoilValue(apiBackendSelectedState);
  const paramValues = useRecoilValue(endpointConfigValueState);

  const [ws, setWs] = useState(null);

  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    if (!ws) {
      setWs(new Ws(`${wsUrlPrefix}/playground`));
    }
  }, [ws, wsUrlPrefix]);

  const runApp = useCallback(
    (sessionId, input) => {
      const requestId = Math.random().toString(36).substring(2);

      setAppRunData((prevState) => ({
        ...prevState,
        isRunning: true,
        isStreaming: false,
        errors: null,
        messages: messagesRef.current.get(),
        input,
      }));

      ws.send(
        JSON.stringify({
          event: "run",
          input,
          id: requestId,
          session_id: sessionId,
        }),
      );
    },
    [ws, setAppRunData],
  );

  const Run = () => {
    return (
      <Button
        type="primary"
        onClick={(e) => {
          runApp(appSessionId.current, {
            input: input,
            config: paramValues,
            bypass_cache: true,
            api_backend_slug: apiBackendSelected.slug,
            api_provider_slug: apiBackendSelected.api_provider.slug,
          });
        }}
        variant="contained"
      >
        {"Run"}
      </Button>
    );
  };

  return (
    <Box sx={{ margin: "10px 2px" }}>
      {showLoginDialog && (
        <LoginDialog
          open={showLoginDialog}
          handleClose={() => setShowLoginDialog(false)}
          redirectPath={window.location.pathname}
        />
      )}
      <Stack>
        <ApiBackendSelector />
        <Grid container spacing={2}>
          <Grid item xs={12} md={4} sx={{ height: "100%" }}>
            <Stack spacing={2}>
              <div style={{ height: "10%" }}>
                <InputForm
                  schema={
                    apiBackendSelected ? apiBackendSelected.input_schema : {}
                  }
                  uiSchema={
                    apiBackendSelected ? apiBackendSelected.input_ui_schema : {}
                  }
                  emptyMessage="Select your API Backend to see the parameters"
                />
              </div>
              <div>{apiBackendSelected && <Run />}</div>
            </Stack>
          </Grid>
          <Grid item xs={12} md={4}>
            <ConfigForm
              schema={
                apiBackendSelected ? apiBackendSelected.config_schema : {}
              }
              uiSchema={
                apiBackendSelected ? apiBackendSelected.config_ui_schema : {}
              }
              formData={paramValues}
              atomState={endpointConfigValueState}
              emptyMessage="Select your API Backend to see the parameters"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Output ws={ws} app={app} />
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
