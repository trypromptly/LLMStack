import React, { useEffect, useRef, useState } from "react";
import { Avatar, Chip, Fab, Grid, Stack } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { Liquid } from "liquidjs";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/mui";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import FileUploadWidget from "../../components/form/DropzoneFileWidget";
import VoiceRecorderWidget from "../form/VoiceRecorderWidget";
import { stitchObjects } from "../../data/utils";
import { LexicalRenderer } from "./lexical/LexicalRenderer";
import { Errors } from "../Output";

import "./WebChatRender.css";
import MarkdownRenderer from "./MarkdownRenderer";

function CustomFileWidget(props) {
  return <FileUploadWidget {...props} />;
}

function CustomVoiceRecorderWidget(props) {
  return <VoiceRecorderWidget {...props} />;
}

const getContentFromMessage = ({ message, app }) => {
  try {
    if (message.role === "bot") {
      return message.content;
    } else {
      return Object.keys(message.content).length === 1
        ? Object.keys(message.content)
            .map((key) => message.content[key])
            .join("\n\n")
        : Object.keys(message.content)
            .map(
              (key) =>
                `**${key}**: ${
                  app &&
                  app?.input_schema &&
                  app?.input_schema?.properties &&
                  app?.input_schema?.properties[key] &&
                  app?.input_schema?.properties[key]?.format === "data-url"
                    ? message.content[key]
                        .split(",")[0]
                        .split(";")[1]
                        .split("=")[1]
                    : message.content[key]
                }`,
            )
            .join("\n\n");
    }
  } catch (e) {
    return "";
  }
};

const MemoizedMessage = React.memo(
  ({ message, index, app, onInMessageFormSubmit }) => {
    return (
      <div
        key={index}
        style={
          message.role === "bot"
            ? {
                display: "flex",
                textAlign: "left",
                fontSize: 16,
                padding: 3,
              }
            : { textAlign: "right" }
        }
      >
        {message.role === "bot" && app?.config?.assistant_image && (
          <Avatar
            src={app.config.assistant_image}
            alt="Bot"
            style={{ margin: "16px 8px 16px 0px" }}
          />
        )}
        {message.role === "bot" && message.content.length <= 1 && (
          <div className="chat_message_from_bot typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <MarkdownRenderer
          className={`chat_message_from_${message.role} ${
            message.error ? "error" : ""
          }`}
          onFormSubmit={onInMessageFormSubmit}
        >
          {getContentFromMessage({ message, app })}
        </MarkdownRenderer>
      </div>
    );
  },
);

export function WebChatRender({ app, isMobile, embed = false, ws }) {
  const [userFormData, setUserFormData] = useState({});
  const [appSessionId, setAppSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [errors, setErrors] = useState(null);
  const [showChat, setShowChat] = useState(!embed);
  const [chatBubbleStyle, setChatBubbleStyle] = useState({
    backgroundColor: app?.config?.window_color,
    color: "white",
    position: "fixed",
    right: 16,
    bottom: 16,
  });
  const templateEngine = new Liquid();
  const outputTemplate = templateEngine.parse(
    app?.output_template?.markdown || "",
  );
  const chunkedOutput = useRef({});
  const chunkedMessages = useRef([]);
  const chatBubbleRef = useRef(null);
  const streamStarted = useRef(true);

  const defaultTheme = createTheme({
    components: {
      MuiInputBase: {
        defaultProps: {
          autoComplete: "off",
        },
      },
      MuiTextField: {
        defaultProps: {
          variant: "outlined",
        },
        styleOverrides: {
          root: {
            "& .MuiOutlinedInput-root": {
              "& > fieldset": {
                border: `1px solid ${app?.config.window_color || "#ccc"}`,
              },
              "&.Mui-focused > fieldset": { border: "1px solid #0f477e" },
              "&:hover > fieldset": { border: "1px solid #0f477e" },
              "&.Mui-error > fieldset": { border: "1px solid #fcc" },
            },
          },
        },
      },
      MuiTypography: {
        styleOverrides: {
          caption: {
            fontSize: "0.7rem",
            marginLeft: 2,
            color: "#666",
          },
        },
      },
      MuiButtonBase: {
        styleOverrides: {
          root: {
            "&.MuiButton-contained": {
              textTransform: "none",
            },
          },
        },
      },
    },
  });

  useEffect(() => {
    if (embed) {
      document.body.style = "background: transparent";
      document.getElementsByClassName("ant-layout")[0].style =
        "background: transparent";

      if (showChat) {
        const userAgent =
          navigator.userAgent || navigator.vendor || window.opera;
        const isMobile =
          /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
            userAgent,
          );
        const width = isMobile ? "100%" : "400px";
        const height = isMobile ? "90vh" : "700px";
        window.parent.postMessage(
          { width, height, type: "promptly-embed-open" },
          "*",
        );
      } else {
        setTimeout(() => {
          window.parent.postMessage(
            {
              type: "promptly-embed-resize",
              width: chatBubbleRef?.current?.clientWidth || "auto",
              height: chatBubbleRef?.current?.clientHeight || "auto",
            },
            "*",
          );
        }, 500);
        window.parent.postMessage({ type: "promptly-embed-close" }, "*");
      }
    }
  }, [embed, showChat]);

  useEffect(() => {
    if (app?.config?.welcome_message && messages.length === 0) {
      setMessages([
        {
          role: "bot",
          content: app.config.welcome_message,
        },
      ]);
    }

    if (
      app?.config?.chat_bubble_text &&
      app?.config?.chat_bubble_style &&
      messages.length === 0
    ) {
      try {
        const style = JSON.parse(app?.config?.chat_bubble_style);
        setChatBubbleStyle((prevBubbleStyle) => ({
          ...prevBubbleStyle,
          ...style,
        }));
      } catch (e) {
        console.error(e);
      }
    }
  }, [app, messages.length]);

  if (ws) {
    ws.setOnMessage((evt) => {
      let error = null;
      const message = JSON.parse(evt.data);
      // Merge the new output with the existing output
      if (message.output) {
        chunkedOutput.current = stitchObjects(
          chunkedOutput.current,
          message.output,
        );
      }

      if (message.event && message.event === "done") {
        streamStarted.current = true;
        return;
      }

      // If we get session info, that means the stream has started
      if (!streamStarted.current && (message.session || message.errors)) {
        streamStarted.current = true;
      }

      if (message.session) {
        setAppSessionId(message.session?.id);
      }

      if (message.errors && message.errors.length > 0) {
        error = message.errors.join("\n\n");
      }

      templateEngine
        .render(outputTemplate, chunkedOutput.current)
        .then((response) => {
          if (response.trim() === "" && error === null) {
            error = "No response from AI. Please try again.";
          }

          chunkedMessages.current = [
            ...chunkedMessages.current.slice(0, -1),
            {
              role: "bot",
              content:
                error !== null
                  ? error || "Unknown error occured. Please try again."
                  : response.trim(),
              error: error !== null,
            },
          ];
          setMessages(chunkedMessages.current);
          error = null;
        });
    });
  }

  const runApp = (input) => {
    setErrors(null);
    setMessages([...messages, { role: "user", content: input }]);

    streamStarted.current = false;
    chunkedOutput.current = {};
    chunkedMessages.current = [
      ...messages,
      { role: "user", content: input },
      { role: "bot", content: "" },
    ];
    ws.send(
      JSON.stringify({
        event: "run",
        input,
        session_id: appSessionId,
      }),
    );
  };

  useEffect(() => {
    const messagesDiv = document.getElementById("messages");
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }, [messages]);

  return (
    <>
      {embed && (
        <Fab
          style={chatBubbleStyle}
          onClick={() => setShowChat(!showChat)}
          variant={app?.config?.chat_bubble_text ? "extended" : "circular"}
          ref={chatBubbleRef}
        >
          {showChat ? (
            <KeyboardArrowDownIcon />
          ) : app?.config?.chat_bubble_text ? (
            <span>{app?.config?.chat_bubble_text}</span>
          ) : (
            <QuestionAnswerIcon />
          )}
        </Fab>
      )}
      <div
        className={`chat-container ${embed ? "embedded" : ""} ${
          showChat ? "maximized" : "minimized"
        }`}
        style={{
          width: isMobile ? "90%" : "100%",
        }}
      >
        {embed && (
          <div
            style={{
              display: "flex",
              backgroundColor: app?.config.window_color,
              borderRadius: "8px 8px 0px 0px",
            }}
          >
            {app?.config?.assistant_image && (
              <Avatar
                src={app.config.assistant_image}
                alt="Bot"
                style={{ margin: "10px 8px", border: "solid 1px #ccc" }}
              />
            )}
            <span
              style={{
                margin: "auto 0px",
                fontWeight: 600,
                fontSize: "18px",
                color: "white",
                padding: app?.config?.assistant_image ? "inherit" : "16px",
              }}
            >
              {app?.name}
            </span>
          </div>
        )}
        <Stack sx={{ padding: "10px", overflow: "auto" }}>
          <LexicalRenderer
            text={app.config?.input_template?.replaceAll(
              "<a href",
              "<a target='_blank' href",
            )}
          />
          <div
            style={{
              marginTop: 10,
              height: isMobile || embed ? "30vh" : "500px",
              overflow: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
            id="messages"
          >
            {messages.map((message, index) => {
              return (
                <MemoizedMessage
                  key={index}
                  message={message}
                  index={index}
                  app={app}
                  onInMessageFormSubmit={(data) => {}}
                />
              );
            })}
            {!streamStarted.current && (
              <div
                style={{
                  display: "flex",
                  textAlign: "left",
                  fontSize: 16,
                  padding: 3,
                }}
              >
                {app?.config?.assistant_image && (
                  <Avatar
                    src={app.config.assistant_image}
                    alt="Bot"
                    style={{ margin: "16px 8px 16px 0px" }}
                  />
                )}
                <div className="chat_message_from_bot typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            {errors && <Errors runError={errors} />}
            {messages.filter((message) => message.role === "user").length ===
              0 &&
              app?.config?.suggested_messages &&
              app?.config?.suggested_messages.length > 0 && (
                <Grid
                  sx={{
                    alignSelf: "flex-end",
                    textAlign: "right",
                    marginTop: "auto",
                  }}
                >
                  {app?.config?.suggested_messages.map((message, index) => (
                    <Chip
                      key={index}
                      label={message}
                      sx={{ margin: "5px 2px" }}
                      onClick={() =>
                        app?.input_schema?.properties &&
                        runApp({
                          [Object.keys(app?.input_schema?.properties)[0]]:
                            message,
                        })
                      }
                    />
                  ))}
                </Grid>
              )}
          </div>
          <ThemeProvider theme={defaultTheme}>
            <Form
              formData={userFormData}
              schema={app.input_schema}
              uiSchema={{
                ...app?.input_ui_schema,
                "ui:submitButtonOptions": {
                  norender:
                    Object.keys(app?.input_schema?.properties).length <= 1 &&
                    Object.keys(app?.input_ui_schema)
                      .map((key) => app?.input_ui_schema[key]?.["ui:widget"])
                      .filter((x) => x === "voice").length === 0
                      ? true
                      : false,
                },
              }}
              validator={validator}
              onSubmit={({ formData }) => {
                if (Object.keys(app?.input_schema?.properties).length > 1) {
                  setUserFormData(formData);
                }
                runApp(formData);
              }}
              widgets={{
                FileWidget: CustomFileWidget,
                voice: CustomVoiceRecorderWidget,
              }}
            />
          </ThemeProvider>
          {embed && (
            <p style={{ textAlign: "center" }}>
              Powered by{" "}
              <a
                href="https://trypromptly.com"
                target="_blank"
                rel="noreferrer"
              >
                Promptly
              </a>
            </p>
          )}
        </Stack>
      </div>
    </>
  );
}
