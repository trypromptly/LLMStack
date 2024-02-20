import React from "react";
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
import { useState } from "react";
import AceEditor from "react-ace";
import ReactMarkdown from "react-markdown";
import Form from "@rjsf/mui";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import { getJSONSchemaFromInputFields } from "../../../data/utils";
import { HeyGenRealtimeAvatar } from "../HeyGenRealtimeAvatar";
import { RemoteBrowserEmbed } from "../../connections/RemoteBrowser";

import "./LayoutRenderer.css";

function PromptlyAppInputForm(props) {
  const { app } = props;
  const { schema, uiSchema } = getJSONSchemaFromInputFields(app?.input_fields);
  const [userFormData, setUserFormData] = useState({});

  return (
    <Form
      schema={schema}
      uiSchema={uiSchema}
      validator={validator}
      formData={userFormData}
      onSubmit={({ formData }) => {
        app._runApp(formData);
        setUserFormData(formData);
      }}
    />
  );
}

const getContentFromMessage = ({ message, inputFields }) => {
  try {
    if (message.type === "app") {
      return message.content;
    } else {
      return Object.keys(message.content).length === 1
        ? Object.keys(message.content)
            .map((key) => message.content[key])
            .join("\n\n")
        : Object.keys(message.content)
            .map((key) => {
              const inputField = inputFields?.find(
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

function AppTypingIndicator({ assistantImage }) {
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
}

function RenderUserMessage(props) {
  const { message, inputFields } = props;

  return (
    <Box className="layout-chat_message_from_user">
      <LayoutRenderer>
        {getContentFromMessage({ message, inputFields })}
      </LayoutRenderer>
    </Box>
  );
}

function RenderAppMessage(props) {
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
}

function PromptlyAppOutputHeader(props) {
  const { app } = props;

  return (
    <Typography
      variant="h6"
      sx={{ marginBottom: 2 }}
      className="section-header"
    >
      Output
      {app?._messages?.length > 1 && !app?._state.isRunning && (
        <Button
          startIcon={<ContentCopyOutlined />}
          onClick={() =>
            navigator.clipboard.writeText(
              app?._messages[app?._messages.length - 1].content,
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
}

function PromptlyAppChatOutput(props) {
  const { app, minHeight, maxHeight } = props;
  const messages = app?._messages || [];

  return (
    <Box
      className="layout-chat-container"
      sx={{ maxHeight, minHeight, overflow: "scroll" }}
    >
      {messages.map((message) => {
        if (message.type === "user") {
          return (
            <RenderUserMessage
              message={message}
              inputFields={app?.input_fields}
              key={message.id}
            />
          );
        }
        return <RenderAppMessage message={message} key={message.id} />;
      })}
      {app?._state?.isRunning && !app?._state?.isStreaming && (
        <AppTypingIndicator />
      )}
    </Box>
  );
}

function PromptlyAppWorkflowOutput(props) {
  const { app, showHeader, placeholder } = props;
  const messages = app?._messages || [];

  return (
    <Box>
      {showHeader && <PromptlyAppOutputHeader app={app} />}
      {!app?._state?.isStreaming &&
        app?._state?.isRunning &&
        !app?._state?.errors && (
          <Box
            sx={{
              margin: "auto",
              textAlign: "center",
            }}
          >
            <CircularProgress />
          </Box>
        )}
      {!app?._state.isRunning &&
        !app?._state.errors &&
        messages.length === 0 &&
        placeholder}
      {messages.length > 0 && messages[messages.length - 1].type === "app" && (
        <RenderAppMessage
          message={messages[messages.length - 1]}
          workflow={true}
        />
      )}
    </Box>
  );
}

export default function LayoutRenderer(props) {
  const runProcessor = props.runProcessor;
  const app = props.app;

  return (
    <ReactMarkdown
      {...props}
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        "promptly-heygen-realtime-avatar": ({ node, ...props }) => {
          return (
            <HeyGenRealtimeAvatar
              node={node}
              {...props}
              runProcessor={runProcessor}
            />
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
          return <PromptlyAppInputForm app={app} />;
        },
        "pa-workflow-output": ({ node, ...props }) => {
          return (
            <PromptlyAppWorkflowOutput
              app={app}
              showHeader={props?.showheader}
              placeholder={props.placeholder}
            />
          );
        },
        "pa-chat-output": ({ node, ...props }) => {
          return (
            <PromptlyAppChatOutput
              app={app}
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
      {props.children || ""}
    </ReactMarkdown>
  );
}
