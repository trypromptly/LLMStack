import { Liquid } from "liquidjs";
import React, {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
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
  const templateEngine = useMemo(() => new Liquid(), []);

  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
  );
  const outputTemplates = useRef([]);
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

  // A Promise that resolves with Message when the template is rendered with incoming data
  const parseIncomingMessage = (
    message,
    chunkedOutput,
    outputTemplate,
    outputTemplates,
    appTypeSlug,
  ) => {
    return new Promise((resolve, reject) => {
      if (message.output.agent) {
        // If it is an agent app, we deal with the step output
        const agentMessage = message.output.agent;
        const template = outputTemplates[agentMessage.from_id];
        let newMessage;

        if (agentMessage.type === "step_error") {
          resolve(
            new AgentStepErrorMessage(
              `${message.id}/${agentMessage.id}`,
              message.request_id,
              agentMessage.content,
              message.reply_to,
            ),
          );

          return;
        }

        templateEngine
          .render(
            template,
            agentMessage.from_id === "agent"
              ? {
                  agent: {
                    content: chunkedOutput[agentMessage.id],
                  },
                }
              : chunkedOutput[agentMessage.id]?.output ||
                  chunkedOutput[agentMessage.id],
          )
          .then((response) => {
            if (agentMessage.type === "step") {
              newMessage = new AgentStepMessage(
                `${message.id}/${agentMessage.id}`,
                message.request_id,
                {
                  ...chunkedOutput[agentMessage.id],
                  output: response,
                },
                message.reply_to,
                !agentMessage.done,
              );
            } else {
              newMessage = new AgentMessage(
                `${message.id}/${agentMessage.id}`,
                message.request_id,
                response,
                message.reply_to,
              );
            }

            resolve(newMessage);
          })
          .catch((error) => {
            reject(error);
          });
      } else {
        templateEngine
          .render(
            outputTemplate,
            appTypeSlug === "playground"
              ? chunkedOutput["processor"]
              : chunkedOutput,
          )
          .then((response) => {
            resolve(
              new AppMessage(
                message.id,
                message.request_id,
                response,
                message.reply_to,
              ),
            );
          })
          .catch((error) => {
            reject(error);
          });
      }
    });
  };

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

      // If we get a templates message, parse it and save the templates
      if (message.templates) {
        let newTemplates = {};
        Object.keys(message.templates).forEach((id) => {
          newTemplates[id] = templateEngine.parse(
            message.templates[id].markdown,
          );
        });
        outputTemplates.current = {
          ...outputTemplates.current,
          ...newTemplates,
        };
      }

      if (message.event && message.event === "done") {
        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
        }));

        if (onEventDone) {
          onEventDone(chunkedOutput.current);
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
        const existingMessageContent =
          messagesRef.current.getContent(message.id) || "";

        const deltas = message.data.deltas;
        const diffs = dmp.diff_fromDelta(
          existingMessageContent,
          deltas["output"],
        );
        const newMessageContent = dmp.diff_text2(diffs);

        messagesRef.current.add(
          new AppMessage(
            message.id,
            message.client_request_id,
            newMessageContent,
          ),
        );

        setAppRunData((prevState) => ({
          ...prevState,
          messages: messagesRef.current.get(),
          isStreaming: newMessageContent !== existingMessageContent,
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
