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
import { stitchObjects } from "../../../data/utils";
import LayoutRenderer from "./LayoutRenderer";
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
import { appRunDataState } from "../../../data/atoms";
import { useSetRecoilState } from "recoil";

const defaultWorkflowLayout = `<pa-layout sx='{"maxWidth": "900px", "margin": "0 auto"}'>
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

const defaultChatLayout = `<pa-layout sx='{"maxWidth": "900px", "margin": "0 auto", "padding": "10px"}'>
    <pa-grid container="true" spacing="2" style="width: 100%">
      <pa-grid item="true" xs="12">
        <pa-chat-output sx='{"height": "calc(100vh - 300px)", "minHeight": "90%"}'></pa-chat-output>
      </pa-grid>
      <pa-grid item="true" xs="12">
        <pa-input-form clearonsubmit="true"></pa-input-form>
      </pa-grid>
    </pa-grid>
</pa-layout>`;

export function AppRenderer({ app, ws }) {
  const appSessionId = useRef(null);
  const [layout, setLayout] = useState("");
  const templateEngine = useMemo(() => new Liquid(), []);

  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
  );
  const outputTemplates = useRef([]);
  const chunkedOutput = useRef({});
  const messagesRef = useRef(new Messages());
  const setAppRunData = useSetRecoilState(appRunDataState);

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
  ) => {
    return new Promise((resolve, reject) => {
      if (message.output.agent) {
        // If it is an agent app, we deal with the step output
        const agentMessage = message.output.agent;
        const template = outputTemplates[agentMessage.from_id];
        let newMessage;

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
                {
                  ...chunkedOutput[agentMessage.id],
                  output: response,
                },
                message.reply_to,
                !agentMessage.done,
              );
            } else if (agentMessage.type === "step_error") {
              newMessage = new AgentStepErrorMessage(
                `${message.id}/${agentMessage.id}`,
                response,
                message.reply_to,
              );
            } else {
              newMessage = new AgentMessage(
                `${message.id}/${agentMessage.id}`,
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
          .render(outputTemplate, chunkedOutput)
          .then((response) => {
            resolve(new AppMessage(message.id, response, message.reply_to));
          })
          .catch((error) => {
            reject(error);
          });
      }
    });
  };

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
      assistantImage: app?.data?.config?.assistant_image,
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
        chunkedOutput.current = {};
      }

      if (message.errors && message.errors.length > 0) {
        message.errors.forEach((error) => {
          messagesRef.current.add(new AppErrorMessage(null, error));
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

        if (message.output.agent) {
          newChunkedOutput = stitchObjects(chunkedOutput.current, {
            [message.output.agent.id]: message.output.agent.content,
          });
        } else {
          newChunkedOutput = stitchObjects(
            chunkedOutput.current,
            message.output,
          );
        }

        chunkedOutput.current = newChunkedOutput;
      }

      if (message.id && message.output) {
        parseIncomingMessage(
          message,
          chunkedOutput.current,
          outputTemplate,
          outputTemplates.current,
        )
          .then((newMessage) => {
            messagesRef.current.add(newMessage);

            setAppRunData((prevState) => ({
              ...prevState,
              messages: messagesRef.current.get(),
              isStreaming: newMessage.content !== null,
            }));
          })
          .catch((error) => {
            console.error("Failed to create message object from output", error);
          });
      }
    });
  }

  const runApp = useCallback(
    (sessionId, input) => {
      chunkedOutput.current = {};
      const requestId = Math.random().toString(36).substring(2);

      messagesRef.current.add(new UserMessage(requestId, input));
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

  const MemoizedLayoutRenderer = memo(
    LayoutRenderer,
    (prevProps, nextProps) => {
      return (
        prevProps.runApp === nextProps.runApp &&
        prevProps.runProcessor === nextProps.runProcessor &&
        prevProps.children === nextProps.children
      );
    },
  );

  return (
    <MemoizedLayoutRenderer runApp={runApp} runProcessor={runProcessor}>
      {layout}
    </MemoizedLayoutRenderer>
  );
}
