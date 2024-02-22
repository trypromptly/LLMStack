import { Liquid } from "liquidjs";
import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactGA from "react-ga4";
import { stitchObjects } from "../../../data/utils";
import LayoutRenderer from "./LayoutRenderer";
import { Messages, UserMessage, AppMessage } from "./Messages";
import { appRunDataState } from "../../../data/atoms";
import { useSetRecoilState } from "recoil";

export function AppRenderer({ app, ws }) {
  const [appSessionId, setAppSessionId] = useState(null);
  const templateEngine = new Liquid();
  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
  );
  const chunkedOutput = useRef({});
  const messagesRef = useRef(new Messages());
  const setAppRunData = useSetRecoilState(appRunDataState);

  useEffect(() => {
    setAppRunData((prevState) => ({
      ...prevState,
      isStreaming: false,
      isRunning: false,
      errors: null,
      inputFields: app?.data?.input_fields,
      messages: messagesRef.current.get(),
    }));

    return () => {
      setAppRunData({});
    };
  });

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
        setAppRunData((prevState) => ({
          ...prevState,
          isStreaming: true,
        }));
      }

      if (message.session) {
        setAppSessionId(message.session.id);
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

      templateEngine
        .render(outputTemplate, chunkedOutput.current)
        .then((response) => {
          if (message.id) {
            messagesRef.current.add(
              new AppMessage(message.id, response, message.reply_to),
            );

            setAppRunData((prevState) => ({
              ...prevState,
              messages: messagesRef.current.get(),
            }));
          }
        });
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

  let layout = app.data?.config?.layout;

  if (!layout) {
    const typeSlug = app?.data?.type_slug;
    if (typeSlug === "text-chat" || typeSlug === "agent") {
      layout = `<pa-layout>
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
    } else {
      layout = `<pa-layout>
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
    }
  }

  return <LayoutRenderer runApp={runApp}>{layout}</LayoutRenderer>;
}
