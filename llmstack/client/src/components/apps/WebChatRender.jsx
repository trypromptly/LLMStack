import React, { useEffect, useRef, useState } from "react";
import { Avatar, Chip, Fab, Grid, Stack, Typography } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { Liquid } from "liquidjs";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/mui";
import { useSetRecoilState } from "recoil";
import { get } from "lodash";
import { streamChunksState } from "../../data/atoms";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import FileUploadWidget from "../../components/form/DropzoneFileWidget";
import VoiceRecorderWidget from "../form/VoiceRecorderWidget";
import { getJSONSchemaFromInputFields, stitchObjects } from "../../data/utils";
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
            .map((key) => {
              const inputField = app?.data?.input_fields?.find(
                (input_field) => input_field.name === key,
              );
              return `**${key}**: ${
                inputField &&
                (inputField.type === "file" ||
                  inputField.type === "voice" ||
                  inputField.type === "image")
                  ? message.content[key]
                      .split(",")[0]
                      .split(";")[1]
                      .split("=")[1]
                  : message.content[key]
              }`;
            })
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
        {message.role === "bot" && app?.data?.config?.assistant_image && (
          <Avatar
            src={app.data?.config?.assistant_image}
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
  (prevProps, curProps) => {
    return prevProps.message?.content === curProps.message?.content;
  },
);

export function WebChatRender({ app, isMobile, embed = false, ws }) {
  const { schema, uiSchema } = getJSONSchemaFromInputFields(
    app?.data?.input_fields,
  );
  const [userFormData, setUserFormData] = useState({});
  const [appSessionId, setAppSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [errors, setErrors] = useState(null);
  const [showChat, setShowChat] = useState(!embed);
  const [chatBubbleStyle, setChatBubbleStyle] = useState({
    backgroundColor: app?.data?.config?.window_color || "#0f477e",
    color: "white",
    position: "fixed",
    right: 16,
    bottom: 16,
  });
  const setStreamChunks = useSetRecoilState(streamChunksState);
  const templateEngine = new Liquid();
  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
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
                border: `1px solid ${app?.data?.config.window_color || "#ccc"}`,
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
      document.getElementsByClassName("root").style = "background: transparent";

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
    if (app?.data?.config?.welcome_message && messages.length === 0) {
      setMessages([
        {
          role: "bot",
          content: app.data?.config?.welcome_message,
        },
      ]);
    }

    if (
      app?.data?.config?.chat_bubble_text &&
      app?.data?.config?.chat_bubble_style &&
      messages.length === 0
    ) {
      try {
        const style = JSON.parse(app?.data?.config?.chat_bubble_style);
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
        const [newChunkedOutput, streamPaths] = stitchObjects(
          chunkedOutput.current,
          message.output,
        );
        chunkedOutput.current = newChunkedOutput;

        // Update streamChunks recoil state
        for (const path of streamPaths) {
          setStreamChunks((prevChunks) => {
            return {
              ...prevChunks,
              [path.replace(/_base64_chunks$/g, "")]: get(
                chunkedOutput.current,
                path,
                null,
              ),
            };
          });
        }
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
          variant={
            app?.data?.config?.chat_bubble_text ? "extended" : "circular"
          }
          ref={chatBubbleRef}
        >
          {showChat ? (
            <KeyboardArrowDownIcon />
          ) : app?.data?.config?.chat_bubble_text ? (
            <span>{app?.data?.config?.chat_bubble_text}</span>
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
              backgroundColor: app?.data?.config.window_color || "#0f477e",
              borderRadius: "8px 8px 0px 0px",
            }}
          >
            {app?.data?.config?.assistant_image && (
              <Avatar
                src={app.data?.config?.assistant_image}
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
                padding: app?.data?.config?.assistant_image
                  ? "inherit"
                  : "16px",
              }}
            >
              {app?.name}
            </span>
          </div>
        )}
        <Stack sx={{ padding: "10px", overflow: "auto" }}>
          <LexicalRenderer
            text={app.data?.config?.input_template?.replaceAll(
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
                {app?.data?.config?.assistant_image && (
                  <Avatar
                    src={app.data?.config?.assistant_image}
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
              app?.data?.config?.suggested_messages &&
              app?.data?.config?.suggested_messages.length > 0 && (
                <Grid
                  sx={{
                    alignSelf: "flex-end",
                    textAlign: "right",
                    marginTop: "auto",
                  }}
                >
                  {app?.data?.config?.suggested_messages.map(
                    (message, index) => (
                      <Chip
                        key={index}
                        label={message}
                        sx={{ margin: "5px 2px" }}
                        onClick={() =>
                          app?.data?.input_fields?.length > 0 &&
                          runApp({
                            [app?.data?.input_fields[0].name]: message,
                          })
                        }
                      />
                    ),
                  )}
                </Grid>
              )}
          </div>
          <ThemeProvider theme={defaultTheme}>
            <Form
              formData={userFormData}
              schema={schema}
              uiSchema={{
                ...uiSchema,
                "ui:submitButtonOptions": {
                  norender:
                    Object.keys(schema?.properties).length <= 1 &&
                    Object.keys(uiSchema)
                      .map((key) => uiSchema[key]?.["ui:widget"])
                      .filter((x) => x === "voice").length === 0
                      ? true
                      : false,
                },
              }}
              validator={validator}
              onSubmit={({ formData }) => {
                if (Object.keys(schema?.properties).length > 1) {
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
            <Typography sx={{ textAlign: "center" }} variant="caption">
              Powered by{" "}
              <a
                href="https://trypromptly.com"
                target="_blank"
                rel="noreferrer"
              >
                Promptly
              </a>
            </Typography>
          )}
        </Stack>
      </div>
    </>
  );
}
