import { Box, Button, Grid, Stack, Tab, Divider } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import ReactGA from "react-ga4";
import React, { lazy, useEffect, useState, useRef, useCallback } from "react";
import { useSetRecoilState } from "recoil";
import { appRunDataState } from "../data/atoms";
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

const ProcessorSelector = lazy(() => import("../components/ProcessorSelector"));
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
  const [tabValue, setTabValue] = React.useState("form");
  const jsonOutput = useRef({});

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setTabValue(newValue);
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
              if (message?.processor) {
                jsonOutput.current = message.processor;
              }
            }}
          />
        </TabPanel>
        <TabPanel value="json" sx={{ padding: "4px" }}>
          <ThemedJsonEditor data={jsonOutput.current} />
        </TabPanel>
      </TabContext>
    </Box>
  );
}

export default function PlaygroundPage() {
  const appSessionId = useRef(null);
  const [showLoginDialog, setShowLoginDialog] = useState(false);
  const [selectedProcessor, setSelectedProcessor] = useState(null);
  const [input, setInput] = useState({});
  const [config, setConfig] = useState({});
  const messagesRef = useRef(new Messages());
  const setAppRunData = useSetRecoilState(appRunDataState);

  const [app, setApp] = useState({
    name: "Playground",
    uuid: null,
    data: {
      type_slug: "playground",
      output_template: selectedProcessor?.output_template || {
        markdown: "{{ processor | json }}",
      },
      config: {
        layout: defaultPlaygroundLayout,
      },
    },
  });

  const [ws, setWs] = useState(null);

  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    if (selectedProcessor) {
      setApp((prevState) => ({
        ...prevState,
        data: {
          ...prevState.data,
          output_template: selectedProcessor.output_template || {
            markdown: "{{ processor | json }}",
          },
        },
      }));

      if (ws) {
        ws.close();
      }
    }
  }, [selectedProcessor, ws]);

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

      ReactGA.event({
        category: "Playground",
        action: "Run",
        label: `${selectedProcessor?.provider?.slug}/${selectedProcessor?.slug}`,
        transport: "beacon",
      });
    },
    [ws, selectedProcessor, setAppRunData],
  );

  const Run = () => {
    return (
      <Button
        type="primary"
        onClick={(e) => {
          runApp(appSessionId.current, {
            input: input,
            config: config,
            bypass_cache: true,
            api_backend_slug: selectedProcessor.slug,
            api_provider_slug: selectedProcessor.provider.slug,
          });
        }}
        variant="contained"
      >
        {"Run"}
      </Button>
    );
  };

  return (
    <Box sx={{ margin: "16px" }}>
      {showLoginDialog && (
        <LoginDialog
          open={showLoginDialog}
          handleClose={() => setShowLoginDialog(false)}
          redirectPath={window.location.pathname}
        />
      )}
      <Stack>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4} sx={{ height: "100%" }}>
            <Stack spacing={2}>
              <ProcessorSelector
                onProcessorChange={(processor) => {
                  setSelectedProcessor(processor);
                  setInput({});
                  setConfig({});
                  messagesRef.current = new Messages();
                  setAppRunData((prevState) => ({
                    ...prevState,
                    isRunning: false,
                    isStreaming: false,
                    errors: null,
                    messages: messagesRef.current.get(),
                    input: {},
                  }));
                }}
              />
              <Divider />
              <div style={{ height: "10%" }}>
                <InputForm
                  schema={
                    selectedProcessor ? selectedProcessor.input_schema : {}
                  }
                  uiSchema={
                    selectedProcessor ? selectedProcessor.input_ui_schema : {}
                  }
                  emptyMessage="Select your API Backend to see the parameters"
                  input={input}
                  setInput={setInput}
                />
              </div>
              <div>{selectedProcessor && <Run />}</div>
            </Stack>
          </Grid>
          <Grid item xs={12} md={4} sx={{ mt: 1 }}>
            <ConfigForm
              schema={selectedProcessor ? selectedProcessor.config_schema : {}}
              uiSchema={
                selectedProcessor ? selectedProcessor.config_ui_schema : {}
              }
              config={config}
              setConfig={setConfig}
              emptyMessage="Select your API Backend to see the parameters"
            />
          </Grid>
          <Grid item xs={12} md={4} sx={{ mt: 1 }}>
            <Output ws={ws} app={app} />
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
