import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ContentCopyOutlined } from "@mui/icons-material";
import { CircularProgress } from "@mui/material";
import {
  Avatar,
  Box,
  Button,
  Container,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import AceEditor from "react-ace";
import ReactMarkdown from "react-markdown";
import Form from "@rjsf/mui";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import { getJSONSchemaFromInputFields } from "../../../data/utils";
import { HeyGenRealtimeAvatar } from "../HeyGenRealtimeAvatar";
import { RemoteBrowserEmbed } from "../../connections/RemoteBrowser";

import "./LayoutRenderer.css";

const PromptlyAppInputForm = memo(
  ({ appInputFields, runApp, submitButtonOptions }) => {
    const { schema, uiSchema } = getJSONSchemaFromInputFields(appInputFields);
    const [userFormData, setUserFormData] = useState({});

    return (
      <Form
        schema={schema}
        uiSchema={{
          ...uiSchema,
          "ui:submitButtonOptions": {
            norender:
              Object.keys(schema?.properties).length <= 1 &&
              !submitButtonOptions &&
              Object.keys(uiSchema)
                .map((key) => uiSchema[key]?.["ui:widget"])
                .filter((x) => x === "voice").length === 0
                ? true
                : false,
            ...submitButtonOptions,
          },
        }}
        validator={validator}
        formData={userFormData}
        onSubmit={({ formData }) => {
          runApp(formData);
          setUserFormData(formData);
        }}
      />
    );
  },
  (prev, next) => {
    return prev === next;
  },
);

const AppTypingIndicator = memo(
  ({ assistantImage }) => {
    return (
      <div
        style={{
          display: "flex",
          textAlign: "left",
          fontSize: 16,
          padding: 3,
        }}
      >
        {assistantImage && (
          <Avatar
            src={assistantImage}
            alt="Assistant"
            style={{ margin: "16px 8px 16px 0px" }}
          />
        )}
        <div className="layout-chat_message_from_app typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    );
  },
  (prev, next) => {
    return prev === next;
  },
);

const RenderUserMessage = memo(
  ({ message, inputFields }) => {
    const getContentFromMessage = useCallback((messageContent, inputFields) => {
      try {
        return Object.keys(messageContent).length === 1
          ? Object.keys(messageContent)
              .map((key) => messageContent[key])
              .join("\n\n")
          : Object.keys(messageContent)
              .map((key) => {
                const inputField = inputFields?.find(
                  (input_field) => input_field.name === key,
                );
                return `**${key}**: ${
                  inputField &&
                  (inputField.type === "file" ||
                    inputField.type === "voice" ||
                    inputField.type === "image")
                    ? messageContent[key]
                        .split(",")[0]
                        .split(";")[1]
                        .split("=")[1]
                    : messageContent[key]
                }`;
              })
              .join("\n\n");
      } catch (e) {
        return "";
      }
    }, []);

    return (
      <Box className="layout-chat_message_from_user">
        <LayoutRenderer>
          {getContentFromMessage(message.content, inputFields)}
        </LayoutRenderer>
      </Box>
    );
  },
  (prev, next) => {
    return prev.message?.hash === next.message?.hash;
  },
);

const RenderAppMessage = memo(
  (props) => {
    const { message, workflow } = props;
    return (
      <Box
        className={
          workflow ? "layout-workflow-output" : "layout-chat_message_from_app"
        }
      >
        <LayoutRenderer>{message.content}</LayoutRenderer>
      </Box>
    );
  },
  (prev, next) => {
    return prev === next;
  },
);

const PromptlyAppOutputHeader = memo(
  ({ appMessages, appState }) => {
    return (
      <Typography
        variant="h6"
        sx={{ marginBottom: 2 }}
        className="section-header"
      >
        Output
        {appMessages?.length > 1 && !appState.isRunning && (
          <Button
            startIcon={<ContentCopyOutlined />}
            onClick={() =>
              navigator.clipboard.writeText(
                appMessages[appMessages.length - 1].content,
              )
            }
            sx={{
              textTransform: "none",
              float: "right",
              margin: "auto",
            }}
          >
            Copy
          </Button>
        )}
      </Typography>
    );
  },
  (prev, next) => {
    return prev === next;
  },
);

const PromptlyAppChatOutput = memo(
  ({
    appInputFields,
    appMessages,
    appState,
    minHeight,
    maxHeight,
    enableAutoScroll = true,
  }) => {
    const messages = useMemo(() => appMessages || [], [appMessages]);
    const messagesContainerRef = useRef(null);
    const memoizedAppInputFields = useMemo(
      () => appInputFields,
      [appInputFields],
    );
    const [autoScroll, setAutoScroll] = useState(enableAutoScroll);

    useEffect(() => {
      if (messagesContainerRef.current && autoScroll) {
        messagesContainerRef.current.scrollTop =
          messagesContainerRef.current.scrollHeight;
      }
    }, [messages, autoScroll]);

    useEffect(() => {
      const messagesContainer = messagesContainerRef.current;

      const handleScroll = () => {
        if (
          messagesContainer &&
          messagesContainer.scrollTop + messagesContainer.clientHeight + 5 <
            messagesContainer.scrollHeight
        ) {
          setAutoScroll(false);
        } else {
          setAutoScroll(true);
        }
      };

      messagesContainer.addEventListener("scroll", handleScroll);
      return () => {
        messagesContainer.removeEventListener("scroll", handleScroll);
      };
    }, []);

    useEffect(() => {
      if (appState?.isRunning && !appState?.isStreaming) {
        setAutoScroll(true);
      }
    }, [appState?.isRunning, appState?.isStreaming]);

    return (
      <Box
        className="layout-chat-container"
        sx={{ maxHeight, minHeight, overflow: "scroll" }}
        ref={messagesContainerRef}
      >
        {messages.map((message) => {
          if (message.type === "user") {
            return (
              <RenderUserMessage
                message={message}
                inputFields={memoizedAppInputFields}
                key={message.id}
              />
            );
          }
          return <RenderAppMessage message={message} key={message.id} />;
        })}
        {appState?.isRunning && !appState?.isStreaming && (
          <AppTypingIndicator />
        )}
      </Box>
    );
  },
  (prev, next) => {
    return prev.appMessages === next.appMessages;
  },
);

const PromptlyAppWorkflowOutput = memo(
  ({
    appMessages,
    appState,
    showHeader,
    placeholder,
    enableAutoScroll = true,
  }) => {
    const messages = useMemo(() => appMessages || [], [appMessages]);
    const messagesContainerRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(enableAutoScroll);
    const [lastScrollY, setLastScrollY] = useState(window.scrollY);

    useEffect(() => {
      if (autoScroll && messagesContainerRef.current) {
        window.scrollTo(0, messagesContainerRef.current.scrollHeight);
      }
    }, [messages, autoScroll]);

    useEffect(() => {
      const handleScroll = () => {
        const currentScrollY = window.scrollY;

        if (
          appState?.isRunning &&
          !appState?.isStreaming &&
          lastScrollY > currentScrollY
        ) {
          setAutoScroll(false);
        }

        setLastScrollY(currentScrollY);
      };

      // Add the event listener
      window.addEventListener("scroll", handleScroll);

      // Clean up function
      return () => {
        window.removeEventListener("scroll", handleScroll);
      };
    }, [lastScrollY, appState?.isRunning, appState?.isStreaming]);

    return (
      <Box ref={messagesContainerRef}>
        {showHeader && (
          <PromptlyAppOutputHeader
            appMessages={appMessages}
            appState={appState}
          />
        )}
        {!appState?.isStreaming && appState?.isRunning && !appState?.errors && (
          <Box
            sx={{
              margin: "auto",
              textAlign: "center",
            }}
          >
            <CircularProgress />
          </Box>
        )}
        {!appState.isRunning &&
          !appState.errors &&
          messages.length === 0 &&
          placeholder}
        {messages.length > 0 &&
          messages[messages.length - 1].type === "app" && (
            <RenderAppMessage
              message={messages[messages.length - 1]}
              workflow={true}
            />
          )}
      </Box>
    );
  },
  (prev, next) => {
    return prev === next;
  },
);

export default function LayoutRenderer({
  appInputFields,
  appMessages,
  appState,
  runApp,
  runProcessor,
  children,
}) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        "promptly-heygen-realtime-avatar": ({ node, ...props }) => {
          return (
            <HeyGenRealtimeAvatar node={node} runProcessor={runProcessor} />
          );
        },
        "promptly-web-browser-embed": ({ node, ...props }) => {
          return <RemoteBrowserEmbed wsUrl={props.wsurl} />;
        },
        "pa-layout": ({ node, ...props }) => {
          return <Box {...props}>{props.children}</Box>;
        },
        "pa-container": ({ node, ...props }) => {
          return <Container {...props}>{props.children}</Container>;
        },
        "pa-typography": ({ node, ...props }) => {
          return <Typography {...props}>{props.children}</Typography>;
        },
        "pa-button": ({ node, ...props }) => {
          return <Button {...props}>{props.children}</Button>;
        },
        "pa-stack": ({ node, ...props }) => {
          return <Stack {...props}>{props.children}</Stack>;
        },
        "pa-grid": ({ node, ...props }) => {
          return <Grid {...props}>{props.children}</Grid>;
        },
        "pa-paper": ({ node, ...props }) => {
          return <Paper {...props}>{props.children}</Paper>;
        },
        "pa-input-form": ({ node, ...props }) => {
          return (
            <PromptlyAppInputForm
              appInputFields={appInputFields}
              runApp={runApp}
              submitButtonOptions={props.submitbuttonoption}
            />
          );
        },
        "pa-workflow-output": ({ node, ...props }) => {
          return (
            <PromptlyAppWorkflowOutput
              appMessages={appMessages}
              appState={appState}
              showHeader={props?.showheader}
              placeholder={props.placeholder}
            />
          );
        },
        "pa-chat-output": ({ node, ...props }) => {
          return (
            <PromptlyAppChatOutput
              appInputFields={appInputFields}
              appMessages={appMessages}
              appState={appState}
              maxHeight={props.maxheight || "400px"}
              minHeight={props.minheight || "200px"}
            />
          );
        },
        a: ({ node, ...props }) => {
          return (
            <a {...props} target="_blank" rel="noreferrer nofollow">
              {props.children}
            </a>
          );
        },
        table: ({ node, ...props }) => {
          return (
            <table
              style={{
                borderCollapse: "collapse",
                border: "1px solid #ccc",
              }}
              {...props}
            >
              {props.children}
            </table>
          );
        },
        tr: ({ node, ...props }) => {
          return (
            <tr
              {...props}
              style={{
                border: "1px solid #ccc",
              }}
            >
              {props.children}
            </tr>
          );
        },
        th: ({ node, ...props }) => {
          return (
            <th
              {...props}
              style={{
                border: "1px solid #ccc",
              }}
            >
              {props.children}
            </th>
          );
        },
        td: ({ node, ...props }) => {
          return (
            <td
              {...props}
              style={{
                border: "1px solid #ccc",
              }}
            >
              {props.children}
            </td>
          );
        },
        code: ({ node, ...codeProps }) => {
          const language = codeProps.className;
          return language ? (
            <Stack sx={{ maxWidth: "90%" }}>
              <Box
                sx={{
                  backgroundColor: "#CCC",
                  padding: "5px",
                  color: "#000",
                  fontWeight: "400",
                  fontSize: "14px",
                  borderRadius: "5px 5px 0px 0px",
                }}
              >
                <Typography sx={{ textTransform: "none" }}>
                  {language?.split("-")[1].charAt(0).toUpperCase() +
                    language?.split("-")[1].slice(1)}
                  <Button
                    startIcon={<ContentCopyOutlined />}
                    sx={{
                      textTransform: "none",
                      padding: "0px 5px",
                      float: "right",
                      color: "#000",
                    }}
                    onClick={() => {
                      navigator.clipboard.writeText(codeProps.children[0]);
                    }}
                  >
                    Copy code
                  </Button>
                </Typography>
              </Box>
              <AceEditor
                mode={language?.split("-")[1] || "text"}
                theme="dracula"
                value={codeProps.children[0]}
                editorProps={{ $blockScrolling: true }}
                setOptions={{
                  useWorker: false,
                  showGutter: false,
                  maxLines: Infinity,
                }}
                style={{
                  borderRadius: "0px 0px 5px 5px",
                  width: "100%",
                }}
              />
            </Stack>
          ) : (
            <code {...codeProps}>{codeProps.children}</code>
          );
        },
      }}
    >
      {children || ""}
    </ReactMarkdown>
  );
}
