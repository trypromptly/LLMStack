import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ContentCopyOutlined } from "@mui/icons-material";
import { CircularProgress } from "@mui/material";
import { Liquid } from "liquidjs";
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
import { visit } from "unist-util-visit";
import { isElement } from "hast-util-is-element";
import { toHtml } from "hast-util-to-html";
import validator from "@rjsf/validator-ajv8";
import AceEditor from "react-ace";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import { useRecoilValue } from "recoil";
import { ProviderIcon } from "../ProviderIcon";
import { getJSONSchemaFromInputFields } from "../../../data/utils";
import { HeyGenRealtimeAvatar } from "../HeyGenRealtimeAvatar";
import { PDFViewer } from "../DocViewer";
import { RemoteBrowserEmbed } from "../../connections/RemoteBrowser";
import { appRunDataState } from "../../../data/atoms";
import ThemedJsonForm from "../../ThemedJsonForm";
import loadingImage from "../../../assets/images/loading.gif";
import { isEqual, get } from "lodash";

import "ace-builds/src-noconflict/mode-json";
import "./LayoutRenderer.css";

const liquidEngine = new Liquid();

const PromptlyAppInputForm = memo(
  ({ runApp, submitButtonOptions, sx, clearOnSubmit = false }) => {
    const appRunData = useRecoilValue(appRunDataState);
    const { schema, uiSchema } = getJSONSchemaFromInputFields(
      appRunData?.inputFields,
    );
    const [userFormData, setUserFormData] = useState({});

    return (
      <ThemedJsonForm
        disableAdvanced={true}
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
          runApp(appRunData?.sessionId, formData);

          if (!clearOnSubmit) {
            setUserFormData(formData);
          }
        }}
        sx={sx}
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

const UserMessage = memo(
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
          {getContentFromMessage(message.content, inputFields) || ""}
        </LayoutRenderer>
      </Box>
    );
  },
  (prev, next) => {
    return prev.message?.hash === next.message?.hash;
  },
);

const AppMessage = memo(
  (props) => {
    const { message, workflow } = props;
    return (
      <Box
        className={
          workflow ? "layout-workflow-output" : "layout-chat_message_from_app"
        }
      >
        <LayoutRenderer>{message.content || ""}</LayoutRenderer>
      </Box>
    );
  },
  (prev, next) => {
    return prev?.message?.hash === next?.message?.hash;
  },
);

const AgentMessage = memo(
  (props) => {
    const { message, workflow } = props;
    return (
      <Box
        className={
          workflow ? "layout-workflow-output" : "layout-chat_message_from_app"
        }
      >
        <LayoutRenderer>{message.content || ""}</LayoutRenderer>
      </Box>
    );
  },
  (prev, next) => {
    return prev?.message?.hash === next?.message?.hash;
  },
);

const AgentStepToolHeader = memo(({ processor, isRunning = true }) => {
  const icon = (
    <ProviderIcon
      provider_slug={processor?.provider_slug}
      style={{ width: "15px", height: "15px" }}
    />
  );

  return (
    <Box className={"layout-chat_message_type_step_header"}>
      Using&nbsp;&nbsp;{icon}&nbsp;
      <i>{processor?.name || processor?.processor_slug}</i>
      {isRunning && (
        <div className="layout-chat_message_from_app step-runner-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      )}
    </Box>
  );
});

const AgentStepMessage = memo(
  (props) => {
    const { message, processors } = props;

    // A util function to format incomplete JSON strings
    const formatJSON = useCallback((jsonString) => {
      try {
        return JSON.stringify(JSON.parse(jsonString), null, 2);
      } catch (e) {
        return jsonString;
      }
    }, []);

    return (
      <Box className="layout-chat_message_type_step">
        {message.content.name && (
          <AgentStepToolHeader
            processor={processors.find(
              (processor) => processor.id === message.content.name,
            )}
            isRunning={message.isRunning}
          />
        )}
        {message.content.arguments && (
          <AceEditor
            mode="json"
            theme="dracula"
            value={formatJSON(
              message.content.arguments.replaceAll("\\n", "\n"),
            )}
            editorProps={{ $blockScrolling: true, $onChangeWrapLimit: 80 }}
            setOptions={{
              useWorker: false,
              showGutter: false,
              maxLines: Infinity,
              wrap: true,
            }}
            style={{
              marginBottom: 10,
              borderRadius: "5px",
              wordWrap: "break-word",
              maxWidth: "75%",
            }}
          />
        )}
        <LayoutRenderer>{message.content.output || ""}</LayoutRenderer>
      </Box>
    );
  },
  (prev, next) => {
    return prev?.message?.hash === next?.message?.hash;
  },
);

const PromptlyAppOutputHeader = memo(
  ({ appMessages, isRunning }) => {
    return (
      <Typography
        variant="h6"
        sx={{ marginBottom: 2 }}
        className="section-header"
      >
        Output
        {appMessages?.length > 1 && !isRunning && (
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
  ({ minHeight, maxHeight, sx, enableAutoScroll = true }) => {
    const appRunData = useRecoilValue(appRunDataState);
    const appMessages = useMemo(
      () => appRunData?.messages || [],
      [appRunData?.messages],
    );
    const messagesContainerRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(enableAutoScroll);

    useEffect(() => {
      if (messagesContainerRef.current && autoScroll) {
        messagesContainerRef.current.scrollTop =
          messagesContainerRef.current.scrollHeight;
      }
    }, [appMessages, autoScroll]);

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
      if (appRunData?.isRunning && !appRunData?.isStreaming) {
        setAutoScroll(true);
      }
    }, [appRunData?.isRunning, appRunData?.isStreaming]);

    return (
      <Box
        className="layout-chat-container"
        sx={{ maxHeight, minHeight, overflow: "scroll", ...sx }}
        ref={messagesContainerRef}
      >
        {appMessages.map((message) => {
          if (message.type === "user") {
            return (
              <UserMessage
                message={message}
                inputFields={appRunData?.inputFields}
                key={message.id}
              />
            );
          } else if (message.subType === "agent") {
            return <AgentMessage message={message} key={message.id} />;
          } else if (message.subType === "agent-step") {
            return (
              <AgentStepMessage
                message={message}
                key={message.id}
                processors={appRunData?.processors}
              />
            );
          } else if (message.subType === "agent-step-error") {
            return (
              <AgentStepMessage
                message={message}
                key={message.id}
                processors={appRunData?.processors}
              />
            );
          }

          return <AppMessage message={message} key={message.id} />;
        })}
        {appRunData?.isRunning && !appRunData?.isStreaming && (
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
  ({ showHeader, placeholder, sx, enableAutoScroll = true }) => {
    const appRunData = useRecoilValue(appRunDataState);
    const appMessages = useMemo(
      () => appRunData?.messages || [],
      [appRunData?.messages],
    );
    const messagesContainerRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(enableAutoScroll);
    const [lastScrollY, setLastScrollY] = useState(window.scrollY);

    useEffect(() => {
      if (autoScroll && messagesContainerRef.current) {
        window.scrollTo(0, messagesContainerRef.current.scrollHeight);
      }
    }, [appMessages, autoScroll]);

    useEffect(() => {
      const handleScroll = () => {
        const currentScrollY = window.scrollY;

        if (
          appRunData?.isRunning &&
          !appRunData?.isStreaming &&
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
    }, [lastScrollY, appRunData?.isRunning, appRunData?.isStreaming]);

    return (
      <Box ref={messagesContainerRef} sx={sx}>
        {showHeader && (
          <PromptlyAppOutputHeader
            appMessages={appMessages}
            isRunning={appRunData?.isRunning}
          />
        )}
        {!appRunData?.isStreaming &&
          appRunData?.isRunning &&
          !appRunData?.errors && (
            <Box
              sx={{
                margin: "auto",
                textAlign: "center",
              }}
            >
              <CircularProgress />
            </Box>
          )}
        {!appRunData.isRunning &&
          !appRunData.errors &&
          appMessages.length === 0 &&
          placeholder}
        {appMessages.length > 0 &&
          appMessages[appMessages.length - 1].type === "app" && (
            <AppMessage
              message={appMessages[appMessages.length - 1]}
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

const parseSxFromProps = (sxString) => {
  let sx = {};

  if (!sxString) return sx;

  if (typeof sxString === "object") return sxString;

  try {
    sx = JSON.parse(sxString);
  } catch (e) {
    console.error("Failed to parse sx from props", e, sxString);
  }

  return sx;
};

// A rephype plugin to parse all the props in the tree and rebuild the props
// If the props contain a `sx` prop and it is a string, parse it to JSON
const parseAndRebuildSxProps = () => {
  return (tree) => {
    visit(tree, (node) => {
      if (node && isElement(node) && node.properties) {
        for (const prop in node.properties) {
          // Checking if prop has a `sx` key and if it's a string
          if (prop === "sx" && typeof node.properties[prop] === "string") {
            node.properties[prop] = parseSxFromProps(node.properties[prop]);
          }
        }
      }
    });
  };
};

// A rephype plugin to replace children of pa-data element with raw html for the liquid engine to parse
const parseAndRebuildDataProps = () => {
  return (tree) => {
    visit(tree, (node) => {
      if (node && isElement(node) && node.tagName === "pa-data") {
        if (node.children && node.children.length > 0) {
          node.properties["content"] = node.children
            .map((child) => toHtml(child))
            .join("");
        }
      }
    });
  };
};

export default function LayoutRenderer({ runApp, runProcessor, children }) {
  const memoizedRemarkPlugins = useMemo(() => [remarkGfm], []);
  const memoizedRehypePlugins = useMemo(
    () => [rehypeRaw, parseAndRebuildSxProps, parseAndRebuildDataProps],
    [],
  );
  const memoizedRunApp = useCallback(runApp, [runApp]);
  const memoizedRunProcessor = useCallback(runProcessor, [runProcessor]);
  const memoizedComponents = useMemo(() => {
    return {
      "promptly-heygen-realtime-avatar": memo(
        ({ node, ...props }) => {
          return (
            <HeyGenRealtimeAvatar
              processor={props?.processor}
              runProcessor={memoizedRunProcessor}
            />
          );
        },
        (prev, next) => prev.props === next.props,
      ),
      "promptly-web-browser-embed": memo(({ node, ...props }) => {
        return <RemoteBrowserEmbed wsUrl={props?.wsurl} />;
      }),
      "pa-layout": memo(
        ({ node, ...props }) => {
          return <Box {...props}>{props.children}</Box>;
        },
        (prev, next) => prev.props === next.props,
      ),
      "pa-container": memo(
        ({ node, ...props }) => {
          return <Container {...props}>{props.children}</Container>;
        },
        (prev, next) => prev.props === next.props,
      ),
      "pa-typography": memo(
        ({ node, ...props }) => {
          return <Typography {...props}>{props.children}</Typography>;
        },
        (prev, next) =>
          prev.node?.children &&
          next.node?.children &&
          prev.node.children.length > 0 &&
          next.node.children.length > 0 &&
          prev.node.children[0].value === next.node.children[0].value,
      ),
      "pa-button": memo(({ node, ...props }) => {
        return <Button {...props}>{props.children}</Button>;
      }),
      "pa-stack": memo(
        ({ node, ...props }) => {
          return <Stack {...props}>{props.children}</Stack>;
        },
        (prev, next) => prev.props === next.props,
      ),
      "pa-grid": memo(
        ({ node, ...props }) => {
          return <Grid {...props}>{props.children}</Grid>;
        },
        (prev, next) => prev.props === next.props,
      ),
      "pa-paper": memo(
        ({ node, ...props }) => {
          return <Paper {...props}>{props.children}</Paper>;
        },
        (prev, next) => prev.props === next.props,
      ),
      "pa-input-form": ({ node, ...props }) => {
        return (
          <PromptlyAppInputForm
            runApp={memoizedRunApp}
            submitButtonOptions={props.submitbuttonoption}
            clearOnSubmit={props.clearonsubmit}
            sx={props.sx || {}}
          />
        );
      },
      "pa-workflow-output": ({ node, ...props }) => {
        let sx = parseSxFromProps(props.sx);

        return (
          <PromptlyAppWorkflowOutput
            showHeader={props?.showheader}
            placeholder={props.placeholder}
            sx={sx}
          />
        );
      },
      "pa-chat-output": ({ node, ...props }) => {
        return (
          <PromptlyAppChatOutput
            maxHeight={props.maxheight || "100%"}
            minHeight={props.minheight || "200px"}
            sx={props.sx || {}}
          />
        );
      },
      "pa-pdf-viewer": ({ node, ...props }) => {
        return <PDFViewer file={props.file} sx={props.sx || {}} />;
      },
      "pa-data": memo(
        ({ node, ...props }) => {
          const prevMemoizedRef = useRef(null);
          const appRunData = useRecoilValue(appRunDataState);

          const layout = useMemo(() => {
            if (!props.content) return "";

            const templateVariables = (
              props.content.match(/{{(.*?)}}/g) || []
            ).map((x) => x.replace(/{{|}}/g, ""));

            let prevTemplateValues = {};
            let currentTemplateValues = {};

            templateVariables.forEach((variable) => {
              prevTemplateValues[variable] = get(
                prevMemoizedRef.current?.appRunData,
                variable,
                "",
              );
              currentTemplateValues[variable] = get(appRunData, variable, "");
            });

            if (isEqual(prevTemplateValues, currentTemplateValues)) {
              return prevMemoizedRef.current?.layout || "";
            }
            return liquidEngine.parseAndRenderSync(props.content, appRunData);
          }, [props.content, appRunData]);

          useEffect(() => {
            prevMemoizedRef.current = {
              layout,
              appRunData,
            };
          }, [layout, appRunData]);

          const memoizedLayoutRenderer = useMemo(
            () => <LayoutRenderer>{layout}</LayoutRenderer>,
            [layout],
          );

          return memoizedLayoutRenderer;
        },
        (prev, next) => prev.node === next.node,
      ),
      a: memo(
        ({ node, ...props }) => {
          return (
            <a {...props} target="_blank" rel="noreferrer nofollow">
              {props.children}
            </a>
          );
        },
        (prev, next) => prev.props === next.props,
      ),
      table: memo(
        ({ node, ...props }) => {
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
        (prev, next) => prev === next,
      ),
      tr: memo(
        ({ node, ...props }) => {
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
        (prev, next) => prev === next,
      ),
      th: memo(
        ({ node, ...props }) => {
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
        (prev, next) => prev === next,
      ),
      td: memo(
        ({ node, ...props }) => {
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
        (prev, next) => prev === next,
      ),
      img: memo(
        ({ node, ...props }) => {
          const { alt, src } = props;
          // We provide alt text and style as altText|style where style is a string
          const [altText, style] = alt.split("|");
          let styleJson = {};
          try {
            styleJson = JSON.parse(style);
          } catch (e) {
            // Do nothing
          }

          return (
            <img
              src={src || loadingImage}
              alt={altText}
              style={{
                ...{
                  display: "block",
                  maxWidth: "100%",
                  boxShadow: "0px 0px 10px 1px #7d7d7d",
                },
                ...styleJson,
              }}
            />
          );
        },
        (prev, next) => prev.props === next.props,
      ),
      code: memo(
        ({ node, ...codeProps }) => {
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
        (prev, next) => prev.props === next.props,
      ),
    };
  }, [memoizedRunApp, memoizedRunProcessor]);

  if (typeof children !== "string") {
    console.trace("LayoutRenderer: children must be a string", children);
  }

  return (
    <ReactMarkdown
      remarkPlugins={memoizedRemarkPlugins}
      rehypePlugins={memoizedRehypePlugins}
      components={memoizedComponents}
      children={children || ""}
    />
  );
}
