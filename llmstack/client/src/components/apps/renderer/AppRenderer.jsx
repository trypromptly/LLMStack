import { Liquid } from "liquidjs";
import React, { useCallback, useRef, useState } from "react";
import ReactGA from "react-ga4";
import { stitchObjects } from "../../../data/utils";
import LayoutRenderer from "./LayoutRenderer";
import { Messages, UserMessage, AppMessage } from "./Messages";

export function AppRenderer({ app, ws }) {
  const [appSessionId, setAppSessionId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [errors, setErrors] = useState(null);
  const templateEngine = new Liquid();
  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
  );
  const chunkedOutput = useRef({});
  const messagesRef = useRef(new Messages());
  const [messages, setMessages] = useState(messagesRef.current.get());

  if (ws) {
    ws.setOnMessage((evt) => {
      const message = JSON.parse(evt.data);
      // Merge the new output with the existing output
      if (message.output) {
        const [newChunkedOutput] = stitchObjects(
          chunkedOutput.current,
          message.output,
        );
        chunkedOutput.current = newChunkedOutput;
        setIsStreaming(true);
      }

      if (message.session) {
        setAppSessionId(message.session.id);
      }

      if (message.event && message.event === "done") {
        setIsRunning(false);
        setIsStreaming(false);
      }

      if (message.errors && message.errors.length > 0) {
        setErrors({ errors: message.errors });
        setIsRunning(false);
        setIsStreaming(false);
      }

      templateEngine
        .render(outputTemplate, chunkedOutput.current)
        .then((response) => {
          if (message.id) {
            messagesRef.current.add(
              new AppMessage(message.id, response, message.reply_to),
            );
            setMessages(messagesRef.current.get());
          }
        });
    });
  }

  const runApp = useCallback(
    (input) => {
      setErrors(null);
      setIsRunning(true);
      setIsStreaming(false);
      chunkedOutput.current = {};
      const request_id = Math.random().toString(36).substring(2);

      messagesRef.current.add(new UserMessage(request_id, input));
      setMessages(messagesRef.current.get());

      ws.send(
        JSON.stringify({
          event: "run",
          input,
          id: request_id,
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
    [appSessionId, ws, app],
  );

  return (
    <LayoutRenderer
      appInputFields={app?.data?.input_fields}
      appMessages={messages}
      appState={{
        isRunning,
        isStreaming,
        errors,
      }}
      runApp={runApp}
      ws={ws}
    >
      {app.data?.config?.layout}
    </LayoutRenderer>
  );
}
