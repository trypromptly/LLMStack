import { Box, Button, Grid, Stack, CircularProgress, Tab } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import React, { lazy, useEffect, useState, useRef, useCallback } from "react";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";
import {
  apiBackendSelectedState,
  endpointConfigValueState,
  endpointSelectedState,
  inputValueState,
  isLoggedInState,
  templateValueState,
  appRunDataState,
} from "../data/atoms";
import {
  Messages,
  AppErrorMessage,
  AppMessage,
} from "../components/apps/renderer/Messages";
import { Ws } from "../data/ws";
import { stitchObjects } from "../data/utils";

import { PromptlyAppWorkflowOutput } from "../components/apps/renderer/LayoutRenderer";

const ApiBackendSelector = lazy(
  () => import("../components/ApiBackendSelector"),
);
const ConfigForm = lazy(() => import("../components/ConfigForm"));
const InputForm = lazy(() => import("../components/InputForm"));
const LoginDialog = lazy(() => import("../components/LoginDialog"));

function Output(props) {
  const [value, setValue] = React.useState("form");

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
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          <Box>
            <PromptlyAppWorkflowOutput showHeader={false} />
          </Box>
        </TabPanel>
      </TabContext>
    </Box>
  );
}

export default function PlaygroundPage() {
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const [input] = useRecoilState(inputValueState);
  const appSessionId = useRef(null);
  const messagesRef = useRef(new Messages());
  const chunkedOutput = useRef({});
  const [showLoginDialog, setShowLoginDialog] = useState(false);
  const setAppRunData = useSetRecoilState(appRunDataState);

  const [apiBackendSelected, setApiBackendSelected] = useRecoilState(
    apiBackendSelectedState,
  );
  const [endpointSelected, setEndpointSelected] = useRecoilState(
    endpointSelectedState,
  );
  const [paramValues, setParamValues] = useRecoilState(
    endpointConfigValueState,
  );
  const [promptValues, setPromptValues] = useRecoilState(templateValueState);
  const [output, setOutput] = useState("");
  const [runError, setRunError] = useState("");
  const [outputLoading, setOutputLoading] = useState(false);
  const [tokenCount, setTokenCount] = useState(null);
  const [processorResult, setProcessorResult] = useState(null);

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

  if (ws) {
    ws.setOnMessage((evt) => {
      const message = JSON.parse(evt.data);

      console.log("Received message", message);

      if (message.session) {
        appSessionId.current = message.session.id;

        // Add messages from the session to the message list
        setAppRunData((prevState) => {
          prevState?.messages?.forEach((message) => {
            messagesRef.current.add(message);
          });

          return {
            ...prevState,
            sessionId: message.session.id,
          };
        });
      }

      if (message.event && message.event === "done") {
        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
        }));

        chunkedOutput.current = {};
      }

      if (message.event && message.event === "ratelimited") {
        messagesRef.current.add(
          new AppErrorMessage(
            null,
            message.request_id,
            "Rate limit exceeded. Please try after sometime.",
          ),
        );

        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
          isRateLimited: true,
          errors: ["Rate limit exceeded"],
          messages: messagesRef.current.get(),
        }));
      }

      if (message.event && message.event === "usagelimited") {
        messagesRef.current.add(
          new AppErrorMessage(
            null,
            message.request_id,
            isLoggedIn
              ? "Usage limit exceeded. Please try after adding more credits."
              : "Usage limit exceeded. Please login to continue.",
          ),
        );

        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
          isUsageLimited: true,
          errors: ["Usage limit exceeded"],
          messages: messagesRef.current.get(),
        }));

        // If the user is not logged in, show the login dialog
        if (!isLoggedIn) {
          setShowLoginDialog(true);
        }
      }

      if (message.errors && message.errors.length > 0) {
        message.errors.forEach((error) => {
          messagesRef.current.add(
            new AppErrorMessage(null, message.request_id, error),
          );
        });

        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
          errors: message.errors,
          messages: messagesRef.current.get(),
        }));
        chunkedOutput.current = {};
      }

      // Merge the new output with the existing output
      if (message.output) {
        let newChunkedOutput = {};
        newChunkedOutput = stitchObjects(chunkedOutput.current, message.output);
        chunkedOutput.current = newChunkedOutput;
      }

      if (message.id && message.output) {
        const newMessage = message.output;
        messagesRef.current.add(
          new AppMessage(
            message.id,
            message.request_id,
            JSON.stringify(message.output),
            message.reply_to,
          ),
        );
        setAppRunData((prevState) => ({
          ...prevState,
          messages: messagesRef.current.get(),
          isStreaming: newMessage.content !== null,
        }));
      }
    });
  }

  // useEffect(() => {
  //   if (appRunData && !appRunData?.isRunning && !appRunData?.isStreaming) {
  //     if (appRunData?.messages) {
  //       const lastMessage =
  //         appRunData?.messages[appRunData?.messages.length - 1];
  //       if (lastMessage) {
  //         setOutputLoading(false);
  //         setProcessorResult(lastMessage?.content?.output);
  //         if (lastMessage?.content?.output) {
  //           if (lastMessage?.content?.output?.generations) {
  //             setOutput(lastMessage?.content?.output?.generations);
  //           } else if (lastMessage?.content?.output?.chat_completions) {
  //             setOutput(lastMessage?.content?.output?.chat_completions);
  //           } else {
  //             setOutput([lastMessage?.content?.output]);
  //           }
  //         }
  //         if (lastMessage?.content?.errors) {
  //           setRunError(lastMessage?.content?.errors);
  //         }
  //       }
  //     }
  //   }
  // }, [appRunData]);

  const runApp = useCallback(
    (sessionId, input) => {
      setRunError("");
      setOutputLoading(true);

      chunkedOutput.current = {};
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

  useEffect(() => {
    setTokenCount(null);
    setOutput("");
  }, [
    setApiBackendSelected,
    setEndpointSelected,
    setParamValues,
    setPromptValues,
  ]);

  useEffect(() => {}, [paramValues, promptValues]);

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
            <Output />
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
