import { Liquid } from "liquidjs";
import React, {
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
  Messages,
  UserMessage,
  AppMessage,
  AgentMessage,
  AgentStepMessage,
  AgentStepErrorMessage,
} from "./Messages";
import { appRunDataState } from "../../../data/atoms";
import { useSetRecoilState } from "recoil";

const defaultWorkflowLayout = `<pa-layout>
<pa-paper style="padding: 10px;">
<pa-grid container="true" spacing="2" style="width: 100%">
  <pa-grid item="true" xs="12">
    <pa-input-form />
  </pa-grid>
  <pa-grid item="true" xs="12">
    <br/>
  </pa-grid>
  <pa-grid item="true" xs="12">
    <pa-workflow-output showHeader="true" />
  </pa-grid>
</pa-grid>
</pa-paper>
</pa-layout>`;

const defaultChatLayout = `<pa-layout>
<pa-paper style="padding: 10px;">
<pa-grid container="true" spacing="2" style="width: 100%">
  <pa-grid item="true" xs="12">
    <pa-chat-output sx='{"height": "70vh", "minHeight": "90%"}'/>
  </pa-grid>
  <pa-grid item="true" xs="12">
    <pa-input-form clearonsubmit="true" />
  </pa-grid>
</pa-grid>
</pa-paper>
</pa-layout>`;

export function AppRenderer({ app, ws }) {
  const [appSessionId, setAppSessionId] = useState(null);
  const [layout, setLayout] = useState("");
  const templateEngine = useMemo(() => new Liquid(), []);

  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
  );
  const outputTemplates = useRef([]);
  const chunkedOutput = useRef({});
  const messagesRef = useRef(new Messages());
  const setAppRunData = useSetRecoilState(appRunDataState);

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
    setAppRunData((prevState) => ({
      ...prevState,
      isStreaming: false,
      isRunning: false,
      errors: null,
      inputFields: app?.data?.input_fields,
      messages: messagesRef.current.get(),
      processors: app?.data?.processors || [],
    }));

    return () => {
      setAppRunData({});
    };
  });

  if (ws) {
    ws.setOnMessage((evt) => {
      const message = JSON.parse(evt.data);

      if (message.session) {
        setAppSessionId(message.session.id);
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
      }

      if (message.errors && message.errors.length > 0) {
        setAppRunData((prevState) => ({
          ...prevState,
          isRunning: false,
          isStreaming: false,
          errors: message.errors,
        }));
      }

      // Merge the new output with the existing output
      if (message.output) {
        setAppRunData((prevState) => ({
          ...prevState,
          isStreaming: true,
        }));

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
            }));
          })
          .catch((error) => {
            console.error("Failed to create message object from output", error);
          });
      }
    });
  }

  const runApp = useCallback(
    (input) => {
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
          session_id: appSessionId,
        }),
      );

      ReactGA.event({
        category: "App",
        action: "Run App",
        label: app?.name,
        transport: "beacon",
      });
    },
    [appSessionId, ws, app, setAppRunData],
  );

  return <LayoutRenderer runApp={runApp}>{layout}</LayoutRenderer>;
}
