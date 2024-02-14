import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import { Avatar, Box, Chip, Fab, Grid, Stack, Typography } from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import Form from "@rjsf/mui";
import validator from "@rjsf/validator-ajv8";
import { Liquid } from "liquidjs";
import { get } from "lodash";
import React, { useEffect, useRef, useState } from "react";
import AceEditor from "react-ace";
import ReactGA from "react-ga4";
import { useSetRecoilState } from "recoil";
import FileUploadWidget from "../../components/form/DropzoneFileWidget";
import { streamChunksState } from "../../data/atoms";
import { getJSONSchemaFromInputFields, stitchObjects } from "../../data/utils";
import VoiceRecorderWidget from "../form/VoiceRecorderWidget";
import { Errors } from "../Output";
import "./AgentRenderer.css";
import { LexicalRenderer } from "./lexical/LexicalRenderer";
import MarkdownRenderer from "./MarkdownRenderer";
import { ProviderIcon } from "./ProviderIcon";

import "ace-builds/src-noconflict/mode-json";

function CustomFileWidget(props) {
  return <FileUploadWidget {...props} />;
}

function CustomVoiceRecorderWidget(props) {
  return <VoiceRecorderWidget {...props} />;
}

const getProcessorInfoFromId = (app, id) => {
  const processor = app?.data?.processors?.find(
    (processor) => processor.id === id,
  );

  return {
    icon: (
      <ProviderIcon
        provider_slug={processor?.provider_slug}
        style={{ width: "15px", height: "15px" }}
      />
    ),
    name: processor?.name || processor?.processor_slug,
  };
};

const StepMessageContent = React.memo(({ messageId, step, app }) => {
  if (!step) {
    return null;
  }

  const processorInfo = getProcessorInfoFromId(app, step.name);

  return (
    <Stack direction={"column"} gap={1}>
      <Box className={"chat_message_from_bot chat_message_type_step"}>
        Using&nbsp;&nbsp;{processorInfo.icon}&nbsp;<i>{processorInfo.name}</i>
        {!step.content && (
          <div className="chat_message_from_bot typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
      </Box>
      <Typography
        variant="caption"
        sx={{ textAlign: "left", fontSize: "0.8rem" }}
      >
        Input
      </Typography>
      {step.arguments && (
        <AceEditor
          mode="json"
          theme="dracula"
          value={step.arguments.replaceAll("\\n", "\n")}
          editorProps={{ $blockScrolling: true }}
          setOptions={{
            useWorker: false,
            showGutter: false,
            maxLines: Infinity,
          }}
          style={{
            marginBottom: 10,
            borderRadius: "5px",
            wordWrap: "break-word",
            maxWidth: "75%",
          }}
        />
      )}
      <Typography
        variant="caption"
        sx={{ textAlign: "left", fontSize: "0.8rem" }}
      >
        Output
      </Typography>
      <MarkdownRenderer
        className="chat_message_type_step_output"
        messageId={messageId}
      >
        {step.content}
      </MarkdownRenderer>
    </Stack>
  );
});

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
            style={{
              margin: `${
                message?.type === "step"
                  ? "0px 8px 16px 0px"
                  : "16px 8px 16px 0px"
              }`,
            }}
          />
        )}
        {message.role === "bot" && message.content.length <= 1 && (
          <div className="chat_message_from_bot typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        {message.role === "bot" && message.type === "step" && (
          <StepMessageContent
            messageId={message.id}
            step={message.content}
            app={app}
          />
        )}
        {message.type !== "step" && (
          <MarkdownRenderer
            className={`chat_message_from_${message.role} ${
              message.error ? "error" : ""
            } chat_message_type_${message.type}`}
            onFormSubmit={onInMessageFormSubmit}
          >
            {getContentFromMessage({ message, app })}
          </MarkdownRenderer>
        )}
      </div>
    );
  },
  (prevProps, curProps) =>
    prevProps.message?.type === "step" &&
    typeof prevProps.message?.content === "object"
      ? prevProps.message?.rendered_content ===
          curProps.message?.rendered_content &&
        prevProps.message?.content?.name === curProps.message?.content?.name &&
        prevProps.message?.content?.arguments ===
          curProps.message?.content?.arguments
      : prevProps.message.content === curProps.message.content,
);

export function AgentRenderer({ app, isMobile, embed = false, ws }) {
  const { schema, uiSchema } = getJSONSchemaFromInputFields(
    app?.data?.input_fields,
  );
  const [userFormData, setUserFormData] = useState({});
  const [appSessionId, setAppSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [errors, setErrors] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);
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
  const templates = useRef({});
  const chunkedOutput = useRef({});
  const chunkedMessages = useRef([]);
  const chatBubbleRef = useRef(null);

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

      // Update templates
      if (message.templates) {
        let newTemplates = {};
        Object.keys(message.templates).forEach((id) => {
          newTemplates[id] = templateEngine.parse(
            message.templates[id].markdown,
          );
        });
        templates.current = { ...templates.current, ...newTemplates };
      }

      // Merge chunks of output
      if (message.output) {
        let newChunkedOutput = {};
        let streamPaths = [];
        if (message.output.agent) {
          [newChunkedOutput, streamPaths] = stitchObjects(
            chunkedOutput.current,
            {
              [message.output.agent.id]: message.output.agent.content,
            },
          );

          // Update streamPaths with message.output.agent.id prefix
          streamPaths = streamPaths.map((path) => {
            return `${message.output.agent.id}.${path}`;
          });
        } else {
          [newChunkedOutput, streamPaths] = stitchObjects(
            chunkedOutput.current,
            message.output,
          );
        }

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
        return;
      }

      if (message.session) {
        setAppSessionId(message.session?.id);
        return;
      }

      if (message.errors && message.errors.length > 0) {
        const totalMessages = chunkedMessages.current.length;
        const lastMessage = chunkedMessages.current[totalMessages - 1];
        let existingMessages = null;
        if (
          totalMessages > 0 &&
          (lastMessage.type === "ui_placeholder" ||
            lastMessage["id"] === message.output?.agent?.id)
        ) {
          existingMessages = [...chunkedMessages.current.slice(0, -1)];
        } else {
          existingMessages = [...chunkedMessages.current];
        }
        chunkedMessages.current = [
          ...existingMessages,
          {
            role: "bot",
            content: message.errors.join("\n\n"),
            type: "error",
            error: true,
            id: message.output?.agent?.id,
          },
        ];

        setMessages(chunkedMessages.current);

        return;
      }

      if (
        message.output.agent &&
        message.output.agent.id &&
        message.output.agent.from_id &&
        templates.current[message.output.agent.from_id]
      ) {
        templateEngine
          .render(
            templates.current[message.output.agent.from_id],
            message.output.agent.from_id === "agent"
              ? {
                  [message.output.agent.from_id]: {
                    content: chunkedOutput.current[message.output.agent.id],
                  },
                }
              : typeof chunkedOutput.current[message.output.agent.id]
                    ?.output === "string"
                ? chunkedOutput.current[message.output.agent.id]
                : chunkedOutput.current[message.output.agent.id]?.output,
          )
          .then((response) => {
            if (response.trim() === "" && error === null) {
              error = "No response from AI. Please try again.";
            }

            const totalMessages = chunkedMessages.current.length;
            const lastMessage = chunkedMessages.current[totalMessages - 1];
            let existingMessages = null;
            if (
              totalMessages > 0 &&
              (lastMessage.type === "ui_placeholder" ||
                lastMessage["id"] === message.output.agent.id)
            ) {
              existingMessages = [...chunkedMessages.current.slice(0, -1)];
            } else {
              existingMessages = [...chunkedMessages.current];
            }
            chunkedMessages.current = [
              ...existingMessages,
              {
                role: "bot",
                content:
                  message.output.agent.type === "step_error"
                    ? message.output.agent.content
                    : message.output.agent.type === "step"
                      ? {
                          ...chunkedOutput.current[message.output.agent.id],
                          ...{ content: response },
                        }
                      : response,
                error: message.output.agent.type === "step_error",
                type: message.output.agent.type || "output",
                id: message.output.agent.id,
                from_id: message.output.agent.from_id,
                rendered_content: response,
              },
            ];
            setMessages(chunkedMessages.current);
            return;
          })
          .catch((e) => {
            console.error(e);
          });
      }
    });
  }

  const runApp = (input) => {
    setErrors(null);
    setAutoScroll(true);
    setMessages([...messages, { role: "user", content: input }]);

    chunkedOutput.current = {};
    chunkedMessages.current = [
      ...messages,
      { role: "user", content: input },
      { role: "bot", content: "", type: "ui_placeholder" },
    ];
    ws.send(
      JSON.stringify({
        event: "run",
        input,
        session_id: appSessionId,
      }),
    );

    ReactGA.event({
      category: "App",
      action: "Run Agent",
      label: app?.name,
      transport: "beacon",
    });
  };

  useEffect(() => {
    const messagesDiv = document.getElementById("messages");

    if (autoScroll) {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  }, [messages, autoScroll]);

  // Figure out the direction of the scroll. If the user has scrolled up, disable auto scroll
  useEffect(() => {
    const messagesDiv = document.getElementById("messages");
    const handleScroll = () => {
      if (
        messagesDiv.scrollTop + messagesDiv.clientHeight + 5 <
        messagesDiv.scrollHeight
      ) {
        setAutoScroll(false);
      } else {
        setAutoScroll(true);
      }
    };

    messagesDiv.addEventListener("scroll", handleScroll);
    return () => {
      messagesDiv.removeEventListener("scroll", handleScroll);
    };
  }, []);

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
        className={`agent-chat-container ${embed ? "embedded" : ""} ${
          showChat ? "agent-maximized" : "minimized"
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
              height: "70vh",
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
                setMessages(chunkedMessages.current);
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
