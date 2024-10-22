import React, { memo, useCallback, useEffect, useRef, useState } from "react";
import ReactGA from "react-ga4";
import { useLocation } from "react-router-dom";
import { diff_match_patch } from "diff-match-patch";
import {
  AppMessage,
  AppErrorMessage,
  AgentMessage,
  AgentStepMessage,
  AgentStepErrorMessage,
  Messages,
  UserMessage,
} from "./Messages";
import { axios } from "../../../data/axios";
import { isLoggedInState, appRunDataState } from "../../../data/atoms";
import { useSetRecoilState, useRecoilValue } from "recoil";
import logo from "../../../assets/promptly-icon.png";

const LayoutRenderer = React.lazy(() => import("./LayoutRenderer"));
const LoginDialog = React.lazy(() => import("../../LoginDialog"));

export const defaultWorkflowLayout = `<pa-layout sx='{"maxWidth": "1200px", "margin": "10px auto"}'>
  <pa-paper style="padding: 10px;">
    <pa-grid container="true" spacing="2" style="width: 100%">
      <pa-grid item="true" xs="12">
        <pa-input-form workflow="true"></pa-input-form>
      </pa-grid>
      <pa-grid item="true" xs="12">
        <br/>
      </pa-grid>
      <pa-grid item="true" xs="12">
        <pa-workflow-output showHeader="true"></pa-workflow-output>
      </pa-grid>
    </pa-grid>
  </pa-paper>
</pa-layout>`;

export const defaultChatLayout = `<pa-layout sx='{"maxWidth": "1200px", "margin": "0 auto", "padding": "0", "height": "100%"}'>
    <pa-grid container="true" spacing="2" sx='{"height": "100%", "flexDirection": "column"}'>
      <pa-grid item="true" xs="12" sx='{"overflow": "auto !important", "flex": "1 1 0 !important", "padding": "0 !important"}'>
        <pa-chat-output></pa-chat-output>
      </pa-grid>
      <pa-grid item="true" xs="12" sx='{"alignSelf": "flex-end", "flex": "0 !important", "width": "100%", "padding": "0 !important"}'>
        <pa-input-form clearonsubmit="true"></pa-input-form>
      </pa-grid>
    </pa-grid>
</pa-layout>`;

export const webPageRenderLayout = `<pa-layout sx='{"maxWidth": "1200px", "margin": "10px auto"}'>  
  <pa-grid container="true" spacing="2" style="width: 100%">
    <pa-grid item="true" xs="12">
      <pa-workflow-output></pa-workflow-output>
    </pa-grid>
  </pa-grid>
</pa-layout>`;

export default function AppRenderer({ app, ws, onEventDone = null }) {
  const appSessionId = useRef(null);
  const location = useLocation();
  const [layout, setLayout] = useState("");
  const [showLoginDialog, setShowLoginDialog] = useState(false);

  const chunkedOutput = useRef({});
  const messagesRef = useRef(new Messages());
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const setAppRunData = useSetRecoilState(appRunDataState);
  const dmp = new diff_match_patch();

  if (ws && ws.messageRef) {
    messagesRef.current = ws.messageRef;
  } else if (ws) {
    ws.messageRef = messagesRef.current;
  }

  if (ws) {
    ws.setOnMessage((evt) => {
      const message = JSON.parse(evt.data);

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

      // Handle asset creation response
      if (message.asset_request_id) {
        setAppRunData((prevState) => ({
          ...prevState,
          assets: {
            ...prevState.assets,
            [message.asset_request_id]: message.asset,
          },
        }));
      }

      if (message.event && message.event === "done") {
        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
        }));

        if (onEventDone) {
          onEventDone(message.data);
        }

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

          ReactGA.event({
            category: "Account",
            action: "Usage Limit Login Prompt",
            label: app?.name,
            transport: "beacon",
          });
        }
      }

      if (message.type && message.type === "output_stream_chunk") {
        // Iterate through keys in message.data.deltas
        Object.keys(message.data.deltas).forEach((key) => {
          const delta = message.data.deltas[key];

          if (key === "output") {
            const messageId = message.id;
            const existingMessageContent =
              messagesRef.current.getContent(messageId) || "";

            const diffs = dmp.diff_fromDelta(existingMessageContent, delta);
            const newMessageContent = dmp.diff_text2(diffs);

            messagesRef.current.add(
              new AppMessage(
                messageId,
                message.client_request_id,
                newMessageContent,
              ),
            );
          } else if (key.startsWith("agent_output__")) {
            const messageId = `${message.id}/${key}`;
            const existingMessageContent =
              messagesRef.current.getContent(messageId) || "";

            const diffs = dmp.diff_fromDelta(existingMessageContent, delta);
            const newMessageContent = dmp.diff_text2(diffs);

            messagesRef.current.add(
              new AgentMessage(
                messageId,
                message.client_request_id,
                newMessageContent,
              ),
            );
          } else if (key.startsWith("agent_tool_calls__")) {
            const messageId = `${message.id}/${key}`;
            const existingMessageContent =
              messagesRef.current.getContent(messageId)?.arguments || "";

            const diffs = dmp.diff_fromDelta(existingMessageContent, delta);
            const newMessageContent = dmp.diff_text2(diffs);

            messagesRef.current.add(
              new AgentStepMessage(
                messageId,
                message.client_request_id,
                {
                  name: key.split("__")[2],
                  id: key.split("__")[3],
                  arguments: newMessageContent,
                },
                message.reply_to,
                false,
              ),
            );
          } else if (key.startsWith("agent_tool_call_output__")) {
            const messageId = `${message.id}/${key.replace(
              "agent_tool_call_output__",
              "agent_tool_calls__",
            )}`;
            const existingMessageContent =
              messagesRef.current.getContent(messageId) || "";

            const diffs = dmp.diff_fromDelta(
              existingMessageContent?.output || "",
              delta,
            );
            const newMessageOutput = dmp.diff_text2(diffs);

            messagesRef.current.add(
              new AgentStepMessage(
                messageId,
                message.client_request_id,
                {
                  ...existingMessageContent,
                  output: newMessageOutput,
                },
                message.reply_to,
              ),
            );
          } else if (key.startsWith("agent_tool_call_done__")) {
            const messageId = `${message.id}/${key.replace(
              "agent_tool_call_done__",
              "agent_tool_calls__",
            )}`;
            const existingMessageContent =
              messagesRef.current.getContent(messageId) || "";

            messagesRef.current.add(
              new AgentStepMessage(
                messageId,
                message.client_request_id,
                existingMessageContent,
                message.reply_to,
                false,
              ),
            );
          } else if (key.startsWith("agent_tool_call_errors__")) {
            const messageId = `${message.id}/${key}`;
            const diffs = dmp.diff_fromDelta("", delta);

            messagesRef.current.add(
              new AgentStepErrorMessage(
                messageId,
                message.client_request_id,
                dmp.diff_text2(diffs),
                message.reply_to,
              ),
            );
          }
        });

        setAppRunData((prevState) => ({
          ...prevState,
          messages: messagesRef.current.get(),
          isStreaming: true,
        }));
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
    });
  }

  const runApp = useCallback(
    (sessionId, input) => {
      chunkedOutput.current = {};
      const requestId = Math.random().toString(36).substring(2);

      messagesRef.current.add(new UserMessage(requestId, null, input));
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
        category: "App",
        action: "Run App",
        label: app?.name,
        transport: "beacon",
      });
    },
    [ws, app, setAppRunData],
  );

  const cancelAppRun = useCallback(() => {
    setAppRunData((prevState) => ({
      ...prevState,
      isRunning: false,
    }));

    if (ws && ws.ws) {
      ws.send(
        JSON.stringify({
          event: "stop",
        }),
      );
    }
  }, [ws, setAppRunData]);

  const runProcessor = useCallback(
    async (sessionId, processorId, input, disable_history = true) => {
      // Do not allow running a processor if there is no session
      if (!sessionId) {
        console.error("No session ID set");
        return;
      }

      const response = await axios().post(
        `/api/apps/${app?.uuid}/processors/${processorId}/run`,
        {
          input,
          session_id: sessionId,
          preview: window.location.pathname.endsWith("/preview"),
          disable_history,
        },
      );

      // Check if output is a string and parse it as JSON
      let output = response?.data?.output;
      if (output && typeof output === "string") {
        try {
          output = JSON.parse(output);
        } catch (e) {
          console.error(e);
        }
      }

      return output;
    },
    [app?.uuid],
  );

  const createAsset = useCallback(
    (assetRequestId, fileName, mimeType, streaming = false) => {
      ws.send(
        JSON.stringify({
          event: "create_asset",
          data: {
            file_name: fileName,
            mime_type: mimeType,
            streaming: streaming,
          },
          id: assetRequestId,
        }),
      );

      ReactGA.event({
        category: "App",
        action: "Create Asset",
        label: `${app?.name} - ${mimeType}`,
        transport: "beacon",
      });

      return;
    },
    [ws, app],
  );

  useEffect(() => {
    // Cancel app run and reset appRunData if location changes
    return () => {
      cancelAppRun();
      setAppRunData({});
    };
  }, [location, cancelAppRun, setAppRunData]);

  useEffect(() => {
    if (app?.data?.config?.layout) {
      setLayout(app?.data?.config?.layout);
    } else {
      setLayout(
        app?.data?.type_slug === "web"
          ? defaultWorkflowLayout
          : defaultChatLayout,
      );
    }
  }, [app?.data?.config?.layout, app?.data?.type_slug]);

  useEffect(() => {
    if (app?.data?.config?.welcome_message) {
      const welcomeMessage = new AppMessage(
        "welcome",
        null,
        app?.data?.config?.welcome_message,
      );
      messagesRef.current.add(welcomeMessage);
    }

    setAppRunData((prevState) => ({
      ...prevState,
      isStreaming: false,
      isRunning: false,
      errors: null,
      inputFields: app?.data?.input_fields,
      appIntroText: app.data?.config?.input_template?.replaceAll(
        "<a href",
        "<a target='_blank' href",
      ),
      messages: messagesRef.current.get(),
      processors: app?.data?.processors || [],
      assistantImage: app?.icon || app?.data?.config?.assistant_image || logo,
      suggestedMessages: app?.data?.config?.suggested_messages || [],
    }));

    return () => {
      setAppRunData({});
      chunkedOutput.current = {};
    };
  });

  useEffect(() => {
    if (
      ws &&
      app?.data?.config?.layout &&
      !appSessionId.current &&
      app?.data?.config?.init_on_load
    ) {
      ws.send(
        JSON.stringify({
          event: "init",
        }),
      );
    }
  }, [ws, app?.data?.config?.layout, app?.data?.config?.init_on_load]);

  const MemoizedLayoutRenderer = memo(
    LayoutRenderer,
    (prevProps, nextProps) => {
      return (
        prevProps.runApp === nextProps.runApp &&
        prevProps.runProcessor === nextProps.runProcessor &&
        prevProps.cancelAppRun === nextProps.cancelAppRun &&
        prevProps.createAsset === nextProps.createAsset &&
        prevProps.children === nextProps.children
      );
    },
  );

  return (
    <>
      {showLoginDialog && (
        <LoginDialog
          open={showLoginDialog}
          handleClose={() => setShowLoginDialog(false)}
          redirectPath={window.location.pathname}
        />
      )}
      <MemoizedLayoutRenderer
        runApp={runApp}
        runProcessor={runProcessor}
        cancelAppRun={cancelAppRun}
        createAsset={createAsset}
      >
        {layout}
      </MemoizedLayoutRenderer>
    </>
  );
}
